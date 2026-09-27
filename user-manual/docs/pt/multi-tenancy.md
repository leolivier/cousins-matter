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

## Aceder a uma família

Todos iniciam sessão na página de início de sessão padrão — a família é resolvida
automaticamente a partir da conta ligada; não existe um URL por família. Um endereço
de e-mail pertence a uma única família: para aderir a outra família é necessário
outro endereço de e-mail.

* **Criador da família**: após o registo em *«Criar uma nova família»*, a conta
  permanece inativa até que a hiperligação do e-mail de verificação seja clicada;
  inicie sessão depois normalmente e será o administrador da família.
* **Outros membros**: ou aceitar o convite enviado por e-mail pelo administrador da
  família (hiperligação vinculada ao tenant → registo → verificação por e-mail), ou
  submeter um pedido de adesão (formulário com captcha) que um administrador da família
  tem de aprovar. Em ambos os casos, inicie sessão depois na página de início de
  sessão padrão.

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
fazer com que a própria base de dados recuse escritas entre tenants. A RLS está ativa quando
`MULTI_TENANT_ENABLED=True` **e** `POSTGRES_RUNTIME_USER` está definido.

**Com Docker**, defina no `.env`:

```
MULTI_TENANT_ENABLED=True
POSTGRES_RUNTIME_USER=cm_app
POSTGRES_RUNTIME_PASSWORD=<palavra-passe forte>
```

e reinicie os contentores da aplicação:

```
docker compose restart cousins-matter qcluster
```

No arranque, o entrypoint executa as migrações **como proprietário**
(`POSTGRES_USER`): a migração RLS (`tenants.0003_rls`) cria o papel de execução com
privilégios apenas de DML e aplica as políticas; em seguida, o servidor e o qcluster
reiniciam e ligam-se com o papel de execução. Nada a executar manualmente.

**Com uma instalação manual (sem Docker)**, defina as mesmas variáveis e execute
`manage.py migrate` **como proprietário** (`POSTGRES_USER`) — é exatamente o que o
entrypoint automatiza acima.

**Para que serve `POSTGRES_USER`**: é o proprietário (superutilizador) criado pela
imagem PostgreSQL. Executa as migrações — cria o papel de execução, os seus privilégios
apenas de DML e as políticas — e, enquanto proprietário, ignora completamente a RLS; é a
razão pela qual `FORCE ROW LEVEL SECURITY` nunca é utilizado. O servidor e o qcluster só o
utilizam como recurso quando `POSTGRES_RUNTIME_USER` não está definido (a RLS não tem então efeito).

Comportamento das políticas para o papel de execução:

* todas as tabelas com âmbito de tenant (galleries, chat, forum, classified ads, polls,
  troves, genealogy, pages): as linhas fora do tenant da sessão são invisíveis **e**
  não graváveis;
* `members_member`: as leituras continuam permissivas (o início de sessão por e-mail ocorre antes de
  o tenant ser conhecido), mas INSERT/UPDATE/DELETE são estritamente limitados ao tenant;
* o middleware define `app.current_tenant_id` por pedido e repõe-no sempre
  de seguida (as ligações agrupadas nunca deixam escapar um tenant); os superutilizadores da plataforma
  recebem `app.bypass` para poderem administrar entre tenants;
* as migrações são executadas como proprietário, o que ignora a RLS — isto é intencional, e é a
  razão pela qual `FORCE ROW LEVEL SECURITY` nunca é utilizado.

## Âmbito atual

Todas as apps do produto têm âmbito de tenant e estão cobertas pela segurança ao nível da
linha: `members`, `galleries`, `chat`, `troves`, `forum`, `classified ads`, `polls`,
`genealogy` e `pages` — 22 tabelas, migrações `tenants.0003_rls` a `tenants.0010_rls_pages`.
Apenas as tabelas de infraestrutura (sessões Django, contas allauth) permanecem globais; o
isolamento ao nível do ORM aplica-se a tudo o resto.
