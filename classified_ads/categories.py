from django.utils.translation import gettext_lazy as _

CATEGORIES = {
  "real_estate": {
    "translation": _("Real estate"),
    "subcategories": {
      "rental": _("Rental"),
      "sale": _("Sale"),
      "house": _("House"),
      "apartment": _("Apartment"),
      "land": _("Land"),
      "commercial": _("Commercial"),
      "collective_housing": _("Collective Housing"),
      "other": _("Other"),
    }
  },
  "vehicles": {
    "translation": _("Vehicles"),
    "subcategories": {
      "cars": _("Cars"),
      "motorcycles": _("Motorcycles"),
      "bicycles": _("Bicycles"),
      "boats": _("Boats"),
      "trucks": _("Trucks"),
      "scooters": _("Scooters"),
      "caravan": _("Caravan"),
      "other": _("Other"),
    }
  },
  "holidays": {
    "translation": _("Holidays"),
    "subcategories": {
      "seasonal_rental": _("Seasonal Rental"),
      "other": _("Other"),
    }
  },
  "job_offers": {
    "translation": _("Job offers"),
    "subcategories": {
      "temporary_job": _("Temporary Job"),
      "open_ended": _("Open Ended Job"),
      "fixed_term": _("Fixed-term contract job offers"),
      "internship": _("Internship"),
      "freelance": _("Freelance"),
      "professional_training": _("Professional Training"),
      "volunteering": _("Volunteering"),
      "other": _("Other"),
    }
  },
  "services": {
    "translation": _("Services"),
    "subcategories": {
      "home_services": _("Home Services"),
      "professional_services": _("Professional Services"),
      "other": _("Other"),
    }
  },
  "mode": {
    "translation": _("Mode"),
    "subcategories": {
      "clothes": _("Clothes"),
      "shoes": _("Shoes"),
      "accessories": _("Accessories"),
      "jewelry": _("Jewelry"),
      "other": _("Other"),
    }
  },
  "home": {
    "translation": _("Home"),
    "subcategories": {
      "furniture": _("Furniture"),
      "decor": _("Decor"),
      "appliances": _("Household Appliances"),
      "tableware": _("Tableware"),
      "linen": _("Household linen"),
      "diy": _("DIY tools and equipment"),
      "garden": _("Garden tools and equipment, plants and seeds"),
      "other": _("Other"),
    }
  },
  "family": {
    "translation": _("Family"),
    "subcategories": {
      "baby_equipment": _("Baby equipment"),
      "baby_clothes": _("Baby clothes"),
      "childrens_furniture": _("Children's furniture"),
      "childrens_clothes": _("Children's clothes"),
      "maternity_clothes": _("Maternity clothes"),
      "childrens_shoes": _("Children's shoes"),
      "childrens_accessories": _("Children's accessories"),
      "toys": _("Toys"),
      "baby_sitting": _("Baby sitting"),
      "other": _("Other"),
    }
  },
  "electronics": {
    "translation": _("Electronics"),
    "subcategories": {
      "computers": _("Computers"),
      "cameras": _("Cameras"),
      "televisions": _("Televisions"),
      "audio": _("Audio"),
      "phones": _("Phones"),
      "game_consoles": _("Game Consoles"),
      "accessories": _("Accessories"),
      "ebook_readers": _("eBook Readers & Tablets"),
      "video_games": _("Video Games"),
      "other": _("Other"),
    }
  },
  "leisure": {
    "translation": _("Leisure"),
    "subcategories": {
      "books": _("Books"),
      "movies": _("Movies"),
      "music": _("Music"),
      "sport": _("Sport"),
      "games": _("Games"),
      "collectibles": _("Collectibles"),
      "tickets": _("Tickets"),
      "instruments": _("Musical Instruments"),
      "models": _("Models"),
      "antiques": _("Antiques"),
      "other": _("Other"),
    }
  },
  "other": {
    "translation": _("Other"),
    "subcategories": {
      "professional_equipment": _("Professional equipment"),
      "pets": _("Pets"),
      "donations": _("Donations"),
      "other": _("Other"),
    }
  }
}
