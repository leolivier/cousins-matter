# Analyse des Requêtes N+1 - Module classified_ads

## Résumé Exécutif

J'ai identifié **2 problèmes N+1 critiques** dans le module `classified_ads` qui peuvent impacter significativement les performances de l'application.

---

## 🔴 Problème N+1 #1 : Liste des Annonces (CRITIQUE)

### Localisation
- **Fichier**: [`classified_ads/views.py`](classified_ads/views.py:75-81)
- **Vue**: `ListAdsView`
- **Template**: [`classified_ads/templates/classified_ads/list.html`](classified_ads/templates/classified_ads/list.html:16-30)

### Description du Problème

Dans la vue `ListAdsView`, le queryset récupère les annonces sans précharger la relation `owner` (ForeignKey vers `Member`):

```python
def get_queryset(self):
  return ClassifiedAd.objects.filter(ad_status=ClassifiedAd.AD_STATUS_FOR_SALE).order_by("-date_created")
```

Ensuite, dans le template [`list.html`](classified_ads/templates/classified_ads/list.html:25), on accède à `ad.owner` pour chaque annonce:

```django
{% blocktranslate with owner=ad.owner date_created=ad.date_created|date:"SHORT_DATE_FORMAT" trimmed %}
Added by {{ owner }} on {{ date_created }}
{% endblocktranslate %}
```

### Impact
- **1 requête** pour récupérer N annonces
- **N requêtes supplémentaires** pour récupérer chaque propriétaire (Member)
- **Total: N+1 requêtes**

Pour 100 annonces, cela génère 101 requêtes SQL au lieu de 2 !

### Solution Recommandée

Utiliser `select_related()` pour précharger la relation `owner`:

```python
def get_queryset(self):
  return (
    ClassifiedAd.objects.filter(ad_status=ClassifiedAd.AD_STATUS_FOR_SALE).select_related("owner").order_by("-date_created")
  )
```

**Gain de performance**: Réduit de N+1 à 2 requêtes (1 JOIN SQL)

---

## 🔴 Problème N+1 #2 : Détail d'une Annonce avec Photos (CRITIQUE)

### Localisation
- **Fichier**: [`classified_ads/views.py`](classified_ads/views.py:83-86)
- **Vue**: `AdDetailView`
- **Template**: [`classified_ads/templates/classified_ads/detail.html`](classified_ads/templates/classified_ads/detail.html:1-77)
- **Template inclus**: [`classified_ads/templates/classified_ads/gallery.html`](classified_ads/templates/classified_ads/gallery.html:27-38)

### Description du Problème

La vue `AdDetailView` utilise le comportement par défaut de `DetailView` sans optimisation:

```python
class AdDetailView(generic.DetailView):
  model = ClassifiedAd
  template_name = "classified_ads/detail.html"
```

Dans le template [`detail.html`](classified_ads/templates/classified_ads/detail.html:17-19), on accède à `ad.owner`:

```django
{% blocktranslate with owner=ad.owner date_created=ad.date_created|date:"SHORT_DATETIME_FORMAT" trimmed %}
Added by {{ owner }} on {{ date_created }}
{% endblocktranslate %}
```

Plus critique encore, dans [`gallery.html`](classified_ads/templates/classified_ads/gallery.html:27), on itère sur `ad.photos.all`:

```django
{% for photo in ad.photos.all %}
    <figure class="image thumbnail gallery-image" data-pk="{{photo.id}}"
            data-fullscreen="{% url 'get_protected_media' photo.image.name%}"
            data-swipe-url="{% url 'classified_ads:get_fullscreen_photo' photo.id%}">
        <img src="{% url 'get_protected_media' photo.thumbnail.name%}" alt="Photo">
    </figure>
{% endfor %}
```

### Impact
- **1 requête** pour récupérer l'annonce
- **1 requête** pour récupérer le propriétaire (owner)
- **1 requête** pour récupérer toutes les photos de l'annonce
- **Total: 3 requêtes** (acceptable mais peut être optimisé à 2)

### Solution Recommandée

Surcharger `get_queryset()` pour précharger les relations:

```python
class AdDetailView(generic.DetailView):
  model = ClassifiedAd
  template_name = "classified_ads/detail.html"

  def get_queryset(self):
    return ClassifiedAd.objects.select_related("owner").prefetch_related("photos")
```

**Gain de performance**: Réduit de 3 à 2 requêtes (1 JOIN + 1 requête pour les photos)

---

## ✅ Points Positifs Identifiés

### 1. Pas de N+1 dans `get_next_prev_photo()`
La fonction [`get_next_prev_photo()`](classified_ads/views.py:107-122) utilise correctement `only()` pour limiter les champs récupérés:

```python
ad_id = AdPhoto.objects.only("ad_id").get(pk=pk).ad_id
```

### 2. Admin Django
L'admin est basique et n'a pas encore de problèmes N+1, mais devrait être optimisé si des listes sont affichées:

```python
# Dans admin.py, ajouter:
class ClassifiedAdAdmin(admin.ModelAdmin):
  list_display = ["title", "owner", "category", "ad_status", "date_created"]
  list_select_related = ["owner"]  # Évite N+1 dans la liste admin


class AdPhotoAdmin(admin.ModelAdmin):
  list_display = ["id", "ad"]
  list_select_related = ["ad"]  # Évite N+1 dans la liste admin
```

---

## 📊 Résumé des Optimisations Recommandées

| Vue | Fichier | Ligne | Problème | Solution | Impact |
|-----|---------|-------|----------|----------|--------|
| `ListAdsView` | [`views.py`](classified_ads/views.py:79) | 79 | N+1 sur `owner` | `select_related('owner')` | 🔴 CRITIQUE |
| `AdDetailView` | [`views.py`](classified_ads/views.py:83) | 83 | Requêtes multiples | `select_related('owner').prefetch_related('photos')` | 🟡 MOYEN |
| Admin | [`admin.py`](classified_ads/admin.py:5-6) | 5-6 | Potentiel N+1 | Ajouter `list_select_related` | 🟢 PRÉVENTIF |

---

## 🎯 Plan d'Action Recommandé

### Priorité 1 (Immédiate)
1. ✅ Corriger `ListAdsView.get_queryset()` avec `select_related('owner')`
2. ✅ Corriger `AdDetailView.get_queryset()` avec `select_related('owner').prefetch_related('photos')`

### Priorité 2 (Court terme)
3. ✅ Améliorer l'admin Django avec `list_select_related`

### Priorité 3 (Monitoring)
4. ✅ Ajouter Django Debug Toolbar en développement pour surveiller les requêtes
5. ✅ Considérer l'ajout de tests de performance pour détecter les régressions

---

## 🔧 Code Complet des Corrections

### Fichier: `classified_ads/views.py`

```python
class ListAdsView(generic.ListView):
  model = ClassifiedAd
  template_name = "classified_ads/list.html"

  def get_queryset(self):
    return (
      ClassifiedAd.objects.filter(ad_status=ClassifiedAd.AD_STATUS_FOR_SALE).select_related("owner").order_by("-date_created")
    )


class AdDetailView(generic.DetailView):
  model = ClassifiedAd
  template_name = "classified_ads/detail.html"

  def get_queryset(self):
    return ClassifiedAd.objects.select_related("owner").prefetch_related("photos")
```

### Fichier: `classified_ads/admin.py`

```python
from django.contrib import admin
from .models import ClassifiedAd, AdPhoto


@admin.register(ClassifiedAd)
class ClassifiedAdAdmin(admin.ModelAdmin):
  list_display = ["title", "owner", "category", "subcategory", "ad_status", "price", "date_created"]
  list_filter = ["ad_status", "category", "date_created"]
  search_fields = ["title", "description", "owner__username"]
  list_select_related = ["owner"]  # Évite N+1
  date_hierarchy = "date_created"


@admin.register(AdPhoto)
class AdPhotoAdmin(admin.ModelAdmin):
  list_display = ["id", "ad", "image"]
  list_select_related = ["ad", "ad__owner"]  # Évite N+1
  search_fields = ["ad__title"]
```

---

## 📈 Estimation de l'Impact Performance

### Avant Optimisation
- **Liste de 100 annonces**: ~101 requêtes SQL
- **Détail d'une annonce avec 5 photos**: ~3 requêtes SQL
- **Temps de réponse estimé**: 200-500ms (selon la latence DB)

### Après Optimisation
- **Liste de 100 annonces**: ~2 requêtes SQL (99 requêtes économisées !)
- **Détail d'une annonce avec 5 photos**: ~2 requêtes SQL (1 requête économisée)
- **Temps de réponse estimé**: 50-100ms (selon la latence DB)

**Gain global**: ~98% de réduction des requêtes sur la liste, ~33% sur le détail

---

## 🧪 Comment Vérifier

### Avec Django Debug Toolbar
```python
# settings.py
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INTERNAL_IPS = ["127.0.0.1"]
```

### Avec logging SQL
```python
# settings.py
LOGGING = {
  "version": 1,
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
    },
  },
  "loggers": {
    "django.db.backends": {
      "handlers": ["console"],
      "level": "DEBUG",
    },
  },
}
```

### Test manuel
```python
from django.test.utils import override_settings
from django.db import connection
from django.test import TestCase


class TestN1Queries(TestCase):
  def test_list_ads_queries(self):
    # Créer 10 annonces de test
    for i in range(10):
      ClassifiedAd.objects.create(...)

    with self.assertNumQueries(2):  # Devrait être 2 après optimisation
      response = self.client.get("/classified_ads/")
      list(response.context["object_list"])  # Force l'évaluation
```

---

## 📚 Ressources

- [Django select_related documentation](https://docs.djangoproject.com/en/stable/ref/models/querysets/#select-related)
- [Django prefetch_related documentation](https://docs.djangoproject.com/en/stable/ref/models/querysets/#prefetch-related)
- [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/)
