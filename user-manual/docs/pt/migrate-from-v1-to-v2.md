# Migrar da versão 1 para a versão 2

## Introdução

A versão 2 do Cousins Matter é uma grande reescrita da versão 1 e não é diretamente compatível com a versão 1. 
Entre as grandes alterações:

* a base de dados foi migrada de sqlite3 para postgresql, para permitir melhor desempenho e melhor escalabilidade.
* o cousins matter é agora composto por, pelo menos, 4 contentores docker:

	* o servidor web
	* a base de dados
	* redis
	* o servidor de tarefas assíncronas

	e exigirá, por isso, o docker compose para funcionar.

## Pré-requisitos

Tem de ter o Cousins Matter v1 instalado e a funcionar no seu sistema.

Também precisará de um ambiente Python 3.14+ para executar o script de migração.

## Procedimento

1. Pare o Cousins Matter v1

	```
	cd <cousins-matter-v1-directory>
	docker compose down
	```

1. Descarregue o script de administração do Cousins Matter

	Substitua, na hiperligação abaixo, o marcador de posição <release\> pela versão atual do Cousins Matter:
![GitHub Release](https://img.shields.io/github/v release/leolivier/cousins-matter?style=for-the-badge&label=current%20release&labelColor=%23f00&color=%23ffff)

	```
	mkdir scripts
	curl -o scripts/manage-cousins-matter.py https://raw.githubusercontent.com/leolivier/cousins-matter/refs/tags/<release>/scripts/manage_cousins_matter.py
	```

1. Execute o script de migração

	```
	python scripts/manage-cousins-matter.py migrate-v1-v2 [-r <release>]
	```

	Se a versão não for indicada, a migração será feita para a versão mais recente da série v2.X (recomendado).

	**Preste atenção ao registo do script de migração!** Ele mostrar-lhe-á o progresso da migração e quaisquer problemas potenciais ou ações a realizar.

1. Atualize as suas configurações

	As configurações do Cousins Matter v2 são diferentes das da v1. Atualize o seu ficheiro .env para corresponder às configurações do Cousins Matter v2.

	As configurações do Cousins Matter v2 estão detalhadas na página [Configurações](settings.md).
	Em particular, a migração atualiza o ficheiro .env.example para corresponder às configurações do Cousins Matter v2. Assim, compare este novo ficheiro .env.example com o seu ficheiro .env e atualize o seu ficheiro .env em conformidade. 
	
	Preste também atenção ao facto de alguns valores predefinidos terem mudado. Por exemplo:

	* ALLOW_MEMBERS_TO_CREATE_MEMBERS e ALLOW_MEMBERS_TO_INVITE_MEMBERS são agora True por predefinição
	* ALLOWED_HOSTS passa a conter, por predefinição, o valor de SITE_DOMAIN ('127.0.0.1,localhost,$SITE_DOMAIN')
	* DARK_MODE é agora False por predefinição
	* SESSION_COOKIE_DOMAIN é agora definido como .$SITE_DOMAIN por predefinição
	* SITE_PORT é agora definido como 0 se SITE_DOMAIN estiver definido, e como 8000 caso contrário

	Além disso, novas variáveis foram acrescentadas ao ficheiro .env, mas têm valores predefinidos razoáveis.

	* POSTGRES_USER=cousinsmatter
	* POSTGRES_DB=cousinsmatter
	* POSTGRES_HOST=postgres
	* POSTGRES_PASSWORD é calculada automaticamente no momento da migração
	* PREVIOUS_SECRET_KEYS é calculada automaticamente no momento da migração (e a SECRET_KEY é renovada)

1. Inicie o Cousins Matter v2

	```
	docker compose pull  # obtém todas as imagens
	docker compose up -d
	```

