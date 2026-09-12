# Outras operações de gestão

## Atualizar o Cousins Matter
### Em produção
Obtenha a última imagem e reinicie os contentores
```
cd cousins-matter
docker compose pull
docker compose up -d
```

### Recompilar a imagem a partir do código-fonte
Consulte como compilar a partir do código-fonte pela primeira vez [aqui](installation.md#compilar-a-partir-do-codigo-fonte).
Para atualizar a imagem a partir do código-fonte, basta fazer:
```
git pull        # atualizar as fontes
uv sync         # sincronizar as dependências
make build      # compilar a imagem
make up         # reiniciar os serviços (isto recompila a imagem antes de reiniciar)
# em alternativa à última linha:
make up4run     # reiniciar os outros serviços, exceto o cousins-matter
make run        # iniciar apenas o cousins-matter fora do docker (útil para depuração)
```

## Renovar a sua chave secreta
De vez em quando (por exemplo, uma vez por mês), deve renovar a chave secreta do Cousins Matter. Para isso, execute o seguinte comando:

```
./manage_cousins_matter.sh rotate-secrets
```

Este comando renovará a chave secreta e atualizará a PREVIOUS_SECRET_KEYS no ficheiro .env.

Como o Cousins Matter não pode alterar a sua própria chave secreta, terá de reiniciar os contentores do Cousins Matter para aplicar a nova chave secreta.

Para isso, execute o seguinte comando:

```
docker compose up -d --force-recreate
```
