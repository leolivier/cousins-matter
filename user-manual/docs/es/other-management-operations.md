# Otras operaciones de gestión

## Actualizar Cousins Matter
### En producción
Descarga la última imagen y reinicia el contenedor
```
cd cousins-matter
docker compose pull
docker compose up -d
```

### Reconstruir la imagen a partir del código fuente
Consulta cómo construir a partir del código fuente por primera vez [aquí](installation.md#construir-a-partir-del-codigo-fuente).
Para actualizar tu imagen a partir del código fuente, simplemente haz:
```
git pull        # actualizar las fuentes
uv sync         # sincronizar las dependencias
make build      # construir la imagen
make up         # reiniciar los servicios (esto reconstruye la imagen antes de reiniciar)
# como alternativa a la última línea:
make up4run     # reinicia los demás servicios, excepto cousins-matter
make run        # inicia cousins-matter únicamente fuera de docker (útil para depurar)
```

## Rotar tu clave secreta
De vez en cuando (por ejemplo, una vez al mes), deberías rotar la clave secreta de Cousins Matter. Para ello, ejecuta el siguiente comando:

```
./manage_cousins_matter.sh rotate-secrets
```

Este comando rotará la clave secreta y actualizará PREVIOUS_SECRET_KEYS en el archivo .env.

Como Cousins Matter no puede cambiar él mismo su clave secreta, tendrás que reiniciar los contenedores de Cousins Matter para aplicar la nueva clave secreta.

Para ello, ejecuta el siguiente comando:

```
docker compose up -d --force-recreate
```
