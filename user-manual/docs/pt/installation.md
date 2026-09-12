# Instalação do Cousins Matter

Isto foi testado em Linux e em Windows+WSL2 com Ubuntu ou Debian + Docker Desktop instalado. (O script de instalação ainda não foi testado em MacOS, mas deverá funcionar com pouquíssimas alterações)

## Instalação em produção

### Pré-requisitos

Se ainda não o fez, instale o Docker no seu servidor:
```
curl https://get.docker.com | sh
```

Também precisará de um ambiente Python 3.14+ para executar o script de administração do Cousins Matter.

### Descarregar e executar o script de administração do Cousins Matter

Substitua, na hiperligação abaixo, o marcador de posição **<release\>** pela versão atual do Cousins Matter:
![GitHub Release](https://img.shields.io/github/v/release/leolivier/cousins-matter?style=for-the-badge&label=current%20release&labelColor=%23f00&color=%23ffff)

```
curl https://raw.githubusercontent.com/leolivier/cousins-matter/refs/tags/<release>/scripts/manage_cousins_matter.py
python manage_cousins_matter.py install [-d <directory>] [-r <release>]
```

* se o diretório -d não for indicado, a instalação será feita no diretório atual
* se a versão -r não for indicada, será instalada a versão mais recente

Este comando irá:

* descarregar os ficheiros necessários ao Cousins Matter;
* criar os diretórios necessários;
* criar o ficheiro base .env a partir de um exemplo;
* executar um editor sobre o ficheiro .env para o adaptar às suas necessidades (consulte a página [Configurações](settings.md)). Em particular, __não se esqueça de acrescentar as informações para criar o superutilizador__.

Este script também pode ajudá-lo a [migrar da versão v1 para a versão v2 do Cousins Matter](migrate-from-v1-to-v2.md) e a [renovar a sua chave secreta de vez em quando](other-management-operations.md#renovar-a-sua-chave-secreta).

Para conhecer os diferentes comandos disponíveis, execute:

```
python manage_cousins_matter.py -h
```

Para obter ajuda sobre um comando específico, execute:
```
python manage_cousins_matter.py <command> -h
```

### Iniciar o Cousins Matter

```
cd <directory>
docker compose up -d
```

__Na primeira vez__, aceda a http://127.0.0.1:8000/members/profile, inicie sessão com a conta de administrador que acaba de criar e complete o seu perfil.

**E está feito!**

## Compilar a partir do código-fonte

* Instale o Docker e o uv, caso ainda não o tenha feito

	```
	curl https://get.docker.com | sh
  pip install uv
	```

* Clone o repositório git:

	```
	git clone https://github.com/leolivier/cousins-matter.git
	cd cousins-matter
	```

**Nota para os contribuidores:** se quiser contribuir para o desenvolvimento do cousins-matter, faça primeiro um fork do projeto no github e clone o seu próprio repositório.

* Crie e sincronize o seu ambiente virtual python:
  ```
  uv sync
	```

* Atualize as suas configurações:
	Copie `.env.example` para `.env` e edite `.env` para definir as propriedades conforme as suas necessidades; consulte a página [Configurações](settings.md).

	Pode criar automaticamente a SECRET_KEY executando o seguinte comando:

	```
	./manage_cousins_matter.sh rotate-secrets
	```

* compile a imagem docker:

	```
	make build t=cousins-matter:local
	```

* Utilize a sua imagem local acrescentando a seguinte linha ao ficheiro .env:
	```
	COUSINS_MATTER_IMAGE=cousins-matter:local
	```

* Inicie tudo:

	```
	make up
	```

### Executar fora do Docker

Se quiser depurar a sua instalação, pode executá-la fora do Docker.

Para isso, em vez de iniciar `make up`, utilize:
```
make up4run  # iniciará os contentores necessários: postgres, redis e qcluster (utilizando a imagem compilada anteriormente)
# para iniciar o cousins-matter em modo de desenvolvimento
make run  # recarregará automaticamente após cada modificação do código
# para executar os testes (sem os testes de UI)
make test [t=<nome do teste>]
# para executar os testes de UI
make test-ui [t=<nome do teste>]
# para conhecer todos os outros comandos make, basta executar
make
```
ou inicie a depuração a partir do seu IDE (o projeto já está configurado para o Visual Studio Code no ficheiro .vscode/launch.json)
