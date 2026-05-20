import factory
import random
import os
from factory.django import DjangoModelFactory
from genealogy.models import Person, Family
from members.tests.factories import MemberFactory


class PersonFactory(DjangoModelFactory):
  class Meta:
    model = Person

  first_name = factory.Faker("first_name")
  last_name = factory.Faker("last_name")
  sex = factory.Iterator(["M", "F"])
  member = factory.SubFactory(MemberFactory)
  birth_date = factory.Faker("date_this_century")
  death_date = factory.Faker("date_this_century")
  birth_place = factory.Faker("city")
  death_place = factory.Faker("city")
  notes = factory.Faker("paragraph")


class FamilyFactory(DjangoModelFactory):
  class Meta:
    model = Family

  partner1 = factory.SubFactory(PersonFactory, sex="M")
  partner2 = factory.SubFactory(PersonFactory, sex="F")
  union_type = "MARR"

  _tree_generated = False

  @factory.post_generation
  def create_children(self, create, extracted, **kwargs):
    if not create or extracted is False:
      return

    # If we are in unit testing, just create 1-2 local children to keep tests fast and isolated
    if os.environ.get("ENVIRONMENT") == "test":
      for _ in range(random.randint(1, 2)):
        PersonFactory(child_of_family=self, member=None)
      return

    # Otherwise, if we are in development/generation mode, build the magnificent 10-generation connected tree ONCE
    if not FamilyFactory._tree_generated:
      FamilyFactory._tree_generated = True
      generate_genealogy_tree(nb_generations=10)


def generate_genealogy_tree(nb_generations=10):
  """
  Generates a rich, connected 10-generation family tree for development
  and generation modes. This keeps the test data realistic and complex.
  """
  from faker import Faker
  from datetime import timedelta

  fake = Faker()

  # We will generate 3 root families
  current_generation_couples = []

  def get_birth_death_dates(generation_nb, gen_length=30, max_life_length=100, nb_generations=11):
    birth_date = fake.date_between(
      start_date=f"-{(nb_generations - generation_nb) * gen_length}y",
      end_date=f"-{(nb_generations - generation_nb) * gen_length - 10}y",
    )
    death_date = fake.date_between(
      start_date=birth_date + timedelta(gen_length), end_date=birth_date + timedelta(max_life_length)
    )
    return birth_date, death_date

  # Generation 1: 3 root couples
  for i in range(3):
    bdate, ddate = get_birth_death_dates(1)
    p1 = PersonFactory(
      sex="M", first_name=f"GrandPa_{i}_G1", last_name=f"Root_{i}", member=None, birth_date=bdate, death_date=ddate
    )

    bdate, ddate = get_birth_death_dates(1)
    p2 = PersonFactory(
      sex="F", first_name=f"GrandMa_{i}_G1", last_name=f"Spouse_{i}", member=None, birth_date=bdate, death_date=ddate
    )
    fam = FamilyFactory(partner1=p1, partner2=p2, create_children=False)
    current_generation_couples.append(fam)
    print(
      "created p1 :",
      p1.last_name,
      p1.first_name,
      p1.birth_date,
      p1.death_date,
      "\n  p2 :",
      p2.last_name,
      p2.first_name,
      p2.birth_date,
      p2.death_date,
    )

  for gen in range(2, nb_generations + 1):
    next_generation_children = []

    # 1. Generate 2 children for each couple in the current generation
    for idx, couple in enumerate(current_generation_couples):
      bdate, ddate = get_birth_death_dates(gen)
      c1 = PersonFactory(
        sex="M",
        first_name=f"Son_{idx + 1}_G{gen}",
        last_name=couple.partner1.last_name,
        child_of_family=couple,
        member=None,
        birth_date=bdate,
        death_date=ddate,
      )
      bdate, ddate = get_birth_death_dates(gen)
      c2 = PersonFactory(
        sex="F",
        first_name=f"Daughter_{idx + 1}_G{gen}",
        last_name=couple.partner1.last_name,
        child_of_family=couple,
        member=None,
        birth_date=bdate,
        death_date=ddate,
      )
      next_generation_children.extend([c1, c2])
      print(
        "created c1 :",
        c1.last_name,
        c1.first_name,
        c1.birth_date,
        c1.death_date,
        "\n  c2 :",
        c2.last_name,
        c2.first_name,
        c2.birth_date,
        c2.death_date,
      )

    # 2. Pair them up to form next generation couples (linking them together)
    next_generation_couples = []

    # Separate children by gender
    males = [c for c in next_generation_children if c.sex == "M"]
    females = [c for c in next_generation_children if c.sex == "F"]

    # Link some of them together (e.g. male from lineage i with female from lineage i+1)
    num_links = min(len(males), len(females)) // 2
    for _ in range(num_links):
      if len(males) >= 2 and len(females) >= 2:
        m = males.pop(0)
        f = females.pop(-1)  # Link opposite ends
        fam = FamilyFactory(partner1=m, partner2=f, create_children=False)
        next_generation_couples.append(fam)

    i = 0
    # For remaining males, marry them to external partners
    while males:
      m = males.pop(0)
      i += 1
      bdate, ddate = get_birth_death_dates(gen)
      f = PersonFactory(
        sex="F",
        first_name=f"Spouse_Ext{i}_G{gen}",
        last_name=fake.last_name(),
        member=None,
        birth_date=bdate,
        death_date=ddate,
      )
      fam = FamilyFactory(partner1=m, partner2=f, create_children=False)
      next_generation_couples.append(fam)
      print(
        "created fam :",
        fam.partner1.last_name,
        fam.partner1.first_name,
        fam.partner1.birth_date,
        fam.partner1.death_date,
        "\n  fam.partner2 :",
        fam.partner2.last_name,
        fam.partner2.first_name,
        fam.partner2.birth_date,
        fam.partner2.death_date,
      )

    # For remaining females, marry them to external partners
    while females:
      f = females.pop(0)
      i += 1
      bdate, ddate = get_birth_death_dates(gen)
      m = PersonFactory(
        sex="M",
        first_name=f"Husband_Ext{i}_G{gen}",
        last_name=fake.last_name(),
        member=None,
        birth_date=bdate,
        death_date=ddate,
      )
      fam = FamilyFactory(partner1=m, partner2=f, create_children=False)
      next_generation_couples.append(fam)
      print(
        "created fam :",
        fam.partner1.last_name,
        fam.partner1.first_name,
        fam.partner1.birth_date,
        fam.partner1.death_date,
        "\n  fam.partner2 :",
        fam.partner2.last_name,
        fam.partner2.first_name,
        fam.partner2.birth_date,
        fam.partner2.death_date,
      )

    # Keep the number of couples to 4 to bound size while retaining rich connectivity
    current_generation_couples = next_generation_couples[:4]
