# Multi-tenancy (várias famílias numa só implantação)

O Cousins Matter pode servir **várias famílias (tenants) a partir de uma única implantação**,
com os dados de cada família isolados. Esta página documenta a funcionalidade do produto e
a sua implantação.

## Ativar a funcionalidade

A funcionalidade está **desativada por predefinição**: uma implantação de família única comporta-se
exatamente como a aplicação clássica. Para a ativar, defina no `.env`:

```
MULTI_TENANT_ENABLED=True
```

Isto monta os URLs `/tenants/` (registo de família + gestão) e mostra a
hiperligação «Criar uma nova família» na página de início de sessão. Quando desativada, tudo isto devolve 404.

## Conceitos

| Conceito | Onde |
|---|---|
| **Família (tenant)** | `tenants.Tenant` — nome, slug, `is_active` |
| **Administrador de família** | `Member.role = "admin"` — gere os membros e as configurações da sua família |
| **Administrador da plataforma** | `is_superuser` — entre tenants, reside no tenant `system`, acesso ao Django-admin (`is_staff`) |
| **Isolamento (primário)** | gestor ORM com âmbito de tenant (`TenantManager`) + `TenantMiddleware` |
| **Isolamento (rede de segurança)** | segurança ao nível da linha do PostgreSQL (ver abaixo) |

Dois tenants são criados por migração e não podem ser eliminados: `default`
(atribuído quando nenhum pode ser determinado) e `system` (lar dos administradores da plataforma).

## Criação de uma família

* **Self-service**: com a funcionalidade ativada, a página de início de sessão oferece
  *«Criar uma nova família»*. O criador regista-se com verificação por e-mail e
  torna-se o administrador da família.
* **Por um administrador da plataforma**: `/tenants/create/` cria a família e pode enviar por e-mail
  um convite (hiperligação vinculada ao tenant) ao seu primeiro administrador.

Um identificador de família (slug) é derivado do seu nome; slugs reservados
(`default`, `system`, `admin`, …) são rejeitados.

## Configurações da família

Um administrador de família edita as configurações da sua família em **Family settings**
(menu pendente da barra de navegação): nome do sítio, logótipo, copyright, rodapé, modo escuro, tamanho da
página PDF, idioma, fuso horário, antecipação dos aniversários, permissões dos membros
(criar/convidar) e a raiz do gráfico genealógico. Os valores iguais às predefinições globais
**não são guardados**, pelo que uma alteração global continua a propagar-se às famílias
que nunca os substituíram. Os e-mails para «o administrador» (formulário de contacto, convites,
notificações de falecimento) são encaminhados para o **administrador da família**.

## Ciclo de vida

* **Desativar** (`/tenants/<slug>/toggle-active/`): os membros da família têm a sessão
  terminada e não podem iniciar sessão até à reativação.
* **Eliminação definitiva** (`/tenants/<slug>/delete/`, ou `manage.py delete_tenant
  <slug>`): remove permanentemente a família e todos os seus dados. Recusa o
  tenant system e qualquer família ainda ativa; exige escrever o slug.

## Segurança ao nível da linha do PostgreSQL (reforço opcional)

O isolamento ao nível do ORM é a camada primária de isolamento. Para uma defesa em profundidade, pode
fazer com que a própria base de dados recuse escritas entre tenants:

1. Escolha um papel que não seja o proprietário, por exemplo `cm_app`, com uma palavra-passe forte.
2. No `.env`, defina `POSTGRES_RUNTIME_USER` / `POSTGRES_RUNTIME_PASSWORD` (e
   mantenha `MULTI_TENANT_ENABLED=True`).
3. Execute `manage.py migrate` **como proprietário** (`POSTGRES_USER`) — a migração
   RLS (`tenants.0003_rls`) cria o papel, concede privilégios apenas de DML
   e as políticas. O entrypoint do contentor faz isto automaticamente:
   a inicialização é executada como proprietário, e só o servidor de longa duração utiliza o
   papel de execução (runtime).

Comportamento das políticas para o papel de execução:

* tabelas com âmbito de tenant fora dos modelos das próprias apps (galleries): as linhas fora
  do tenant da sessão são invisíveis **e** não graváveis;
* `members_member`: as leituras continuam permissivas (o início de sessão por e-mail ocorre antes de
  o tenant ser conhecido), mas INSERT/UPDATE/DELETE são estritamente limitados ao tenant;
* o middleware define `app.current_tenant_id` por pedido e repõe-no sempre
  de seguida (as ligações agrupadas nunca deixam escapar um tenant); os superutilizadores da plataforma
  recebem `app.bypass` para poderem administrar entre tenants;
* as migrações são executadas como proprietário, o que ignora a RLS — isto é intencional, e é a
  razão pela qual `FORCE ROW LEVEL SECURITY` nunca é utilizado.

## Âmbito atual

Hoje, `members` e `galleries` têm âmbito de tenant. A conversão das restantes
apps (chat, forum, polls, classified ads, pages, troves, genealogy) segue
o mesmo padrão (classe base `TenantModel` + índices compostos); até lá, os dados dessas
apps são partilhados entre as famílias de uma implantação.
