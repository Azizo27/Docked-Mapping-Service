# Travail Longitudinal

## Contexte

Ce projet a été développé par l'équipe 27 pour la matière GLO-4035 à la session d'Automne 2023 à l'université Laval

## Prérequis

Assurez-vous d'avoir les éléments suivants installés sur votre système :

- Docker : [Guide d'installation Docker](https://docs.docker.com/get-docker/)
- Docker Compose : [Guide d'installation Docker Compose](https://docs.docker.com/compose/install/)

## Requête @GET /heartbeat

La requête `@GET /heartbeat` ne nécessite aucun paquet (payload) et retourne le JSON suivant :
``` 
  {
    "villeChoisie": str
  }
```
Où la valeur de la clé villeChoisie est une chaîne de caractère qui correspond au nom de la ville choisie pour l’application.

### Exemple
``` 
  {
    "villeChoisie": "Quebec City"
  }
```

## Requête @GET /extracted_data
La requête `@GET /extracted_data` ne nécessite aucun paquet (payload) et retourne le JSON suivant :
```
 {
 "nbRestaurants": int ,
 "nbSegments": int
 }
```
Où la valeur de la clé nbRestaurants est un nombre entier qui correspond au nombre de restaurants contenu dans la base de données pour l’application et la valeur de la clé nbSegments est un nombre entier qui correspond au nombre de segments dans la base de données pour l’application.

### Exemple
```
 {
 "nbRestaurants": 904 ,
 "nbSegments": 5300
 }
```

## Requête @GET /transformed_data
La requête `@GET /transformed_data` ne nécessite aucun paquet (payload) et retourne le JSON suivant :
```
 {
 "restaurants": {
 $type1: int ,
 $type2: int ,
 ...
 },
 "longueurCyclable": float
 }
```

Où la valeur de la clé restaurants est un objet en format JSON qui contient le nombre de restaurants par type de restaurants et par type de service dans la base de données de points de restaurants transformés de l’application. Un type est une clé et la valeur est le nombre (un entier). La valeur de la clé longueurCyclable est la valeur numérique qui correspond à la longueur totale des chemins pouvant être utilisés par l’application (c.-à-d. les routes cyclables).

### Exemple
```
 {
 "restaurants": {
 American: 14 ,
 Cambodian: 9 ,
 },
 "longueurCyclable": 83451,5
 }
```

## Requête @GET /readme

La requête `@GET /readme` ne nécessite aucun paquet (payload) et retourne le fichier README.md (en format Markdown). Ce fichier contient toutes les requêtes possibles de l’application, les réponses attendues (les formats) et des exemples de réponse aux requêtes.

## Requête @GET /type

La requête `@GET /type` permet d'obtenir la liste de tous les types de parcours disponibles dans la base de données de l'application. Aucun paquet (payload) n'est requis pour cette requête.

La réponse à la requête sera une liste de chaînes de caractères représentant les types de parcours disponibles.

```
[
  "Type1",
  "Type2",
  "Type3",
  ...
]
```
### Exemple
``` 
[
  "Arabic",
  "Spanish",
  "Japanese"
]
```

## Requête @POST /starting_point

La requête `@POST /starting_point` nécessite un paquet (payload) au format JSON, avec les propriétés suivantes :

``` 
    {
    "length": int,     // Longueur en mètres
    "type": [          // Liste des types de restaurants
        str,
        str,
        ...
    ]
    }
```

La requête retourne le JSON suivant :

``` 
{
  "startingPoint": {
    "type": "Point",              // Type de l'objet géographique
    "coordinates": [float, float] // Coordonnées géographiques (latitude, longitude)
  }
}
```

La valeur de la clé "startingPoint" est un objet géographique de type GeoPoint. Cet objet représente un point de départ aléatoire d'une longueur correspondant à la length du paquet de la requête ±10%. Ce point de départ inclut des restaurants qui appartiennent aux types définis dans la liste type. Si la liste type est vide, tous les types de restaurants sont considérés comme possibles pour la construction du trajet.

### Exemple d'entrée
``` 
    {
    "length": 1500,
    "type": ["italian", "vegetarian"]
    }
```
### Exemple de retour
``` 
{
  "startingPoint": {
    "type": "Point",
    "coordinates": [40.730610, -73.935242]
  }
}
```



## Requête @POST /parcours

La requête `@POST /parcours` nécessite un paquet (payload) au format JSON, avec les propriétés suivantes :

``` 
{
 "startingPoint": {
 "type": "Point",
 "coordinates": [
 float , float
 ]
 },
 "length": int (en metre),
 "numberOfStops": int ,
 "type": [
 str ,
 str ,
 ...
 ]
 }
```

La requête retourne le JSON suivant :

``` 
{
 "type": "FeatureCollection",
 "features": [
 {
 "type": "Feature",
 "geometry": {
 "type": "Point",
 "coordinates": [
float , float
 ]
 },
 "properties": {
 "name": str ,
 "type": str
 }
 },
 ...,
 {
 "type": "Feature",
 "geometry": {
 "type": "MultiLineString",
 "coordinates": [
 [
 [
 float , float
 ],
 [
 float , float
 ],
 [
 float , float
 ],
 ...
 ]
 ]
 },
 "properties": {
 "length": float (en metres)
 }
 }
 ]
 }
```

Où les éléments du JSON est un objet GeoJSON de type (contenu de la clé "type") FeatureCollection, soit une liste d’éléments géographiques. Ces éléments sont une composition de Point et de MultiLineString.
— Un Point est une représentation d’un restaurant. Ses propriétés "name" et "type" sont respectivement le nom et le type de restaurant.
— Un MultiLineString est une représentation d’un segment cyclable. Sa propriété "length", est sa longueur en mètres.
Cet objet GeoJSON correspond à un trajet partant d’un point dans un rayon de 500 mètres du point startingPoint du paquet de la requête, dont le trajet obtenu est d’une longueur de length ±10% avec comme critère de préférence, numberOfStops arrêts qui sont des restaurants inclus dans les types définis dans la liste type. À noter que si la liste type est vide, il est assumé que tous les types de restaurants sont possibles pour la construction du trajet.

### Exemple d'entrée
``` 
{
 "startingPoint": {
 "type": "Point",
 "coordinates": [40.730610, -73.935242]
 },
 "length": 8000,
 "numberOfStops": 3 ,
 "type": [ "italian" , "vegetarian" ]
 }
```

### Exemple de retour
``` 
{
 "type": "FeatureCollection",
 "features": [
 {
 "type": "Feature",
 "geometry": {
 "type": "Point",
  "coordinates": [46.809244, -71.221158]
 },
 "properties": {
 "name": "Buvette Scott" ,
 "type": "Bars"
 }
 },
 {
 "type": "Feature",
 "geometry": {
 "type": "MultiLineString",
 "coordinates": [
 [
[46.81125, -71.20789],
[46.609244, -73.22128],
[45.809244, -71.5448],
 ]
 ]
 },
 "properties": {
 "length": 154.8
 }
 }
 ]
 }
```


## Auteurs
Abdelaziz Abdelkefi , Shelly Caprice , Boubacar Hama Bague , Baptiste Benoit Lefebvre