## Funcionalidades

### Gestão dos membros

* Os membros podem ser listados, filtrados por nome próprio e apelido, e ordenados

	![membros](assets/members.webp)

* O administrador do sítio ou qualquer membro (conforme as configurações) pode convidar outros membros por e-mail

	![convite](assets/invite.webp)

* Qualquer pessoa pode pedir um convite, que será enviado por e-mail ao administrador do sítio, o qual poderá então convidá-la. Os pedidos de convite são protegidos por um captcha.

	![pedido de convite](assets/request-invite.webp)

* Os membros podem criar membros «geridos», ou seja, membros que não estão ativos no sítio (por exemplo, crianças pequenas ou pessoas idosas)
* Os membros geridos podem ser ativados pelos membros que os gerem (por exemplo, quando uma criança já tem idade para estar ativa no sítio).
* Os membros podem ser importados em massa através de ficheiros CSV
* Os membros podem atualizar o seu próprio perfil e o perfil dos membros que gerem
* Os membros podem ser assinalados como falecidos, com uma data de falecimento (útil para a genealogia e a história da família)

	![perfil](assets/profile.webp)

* Um diretório dos membros pode ser impresso em formato PDF

	![diretório](assets/directory.webp)

* Os aniversários dos próximos 50 dias podem ser apresentados (50 pode ser alterado nas configurações)

	![aniversários](assets/birthdays.webp)

### Autenticação

* Autenticação padrão por e-mail/palavra-passe
* Autenticação OAuth/SSO com vários fornecedores:
	* Google
	* Facebook
	* Apple
	* GitHub
	* PocketID (OpenID Connect auto-hospedado)
	* Qualquer fornecedor compatível com OpenID Connect
* Consulte [Autenticação OAuth](oauth-authentication.md) para a configuração detalhada

### Segurança e histórico de início de sessão

* Todas as tentativas de início de sessão são registadas automaticamente com geolocalização por IP
* O histórico de inícios de sessão é guardado para auditoria de segurança (visível para os administradores do sítio no admin do Django)
* Purga automática dos registos de início de sessão antigos após um período de retenção configurável
* Ajuda os administradores a detetar tentativas de acesso não autorizado

### Seguidores e notificações

* Os membros podem seguir outros membros para serem notificados das suas atividades
* Os membros podem seguir salas de conversa, fóruns, galerias e outros conteúdos
* Notificações por e-mail automáticas quando o conteúdo seguido é atualizado
* Frequência de notificação configurável por membro:
	* **Imediata** - Receber as notificações assim que os eventos ocorrem
	* **Horária** - Receber um resumo dos eventos a cada hora
	* **Diária** - Receber um resumo diário dos eventos
	* **Semanal** - Receber um resumo semanal
	* **Mensal** - Receber um resumo mensal
	* **Nunca** - Desativar completamente as notificações
* Cada membro pode configurar a sua frequência de notificação preferida nas configurações do seu perfil
* O agrupamento das notificações reduz a sobrecarga de e-mails, mantendo os membros informados

### Galerias

* Todos os membros ativos podem criar galerias e adicionar-lhes fotos e vídeos
* As galerias podem ter subgalerias de qualquer profundidade
* As fotos e os vídeos podem ser importados em massa através de ficheiros zip. Cada pasta do ficheiro zip torna-se uma galeria. As atualizações são geridas
* A apresentação das fotos da galeria é paginada
* As fotos e os vídeos podem ser apresentados em ecrã inteiro e como diapositivos com um intervalo configurável

### Fórum

* Os membros ativos podem criar publicações
* Os membros ativos podem responder às publicações de outros membros ou adicionar simples comentários

### Conversa (chat)

* Os membros ligados podem conversar em direto com outros membros ligados
* O Cousins Matter gere tantas salas de conversa quantas as solicitadas
* Os membros podem criar salas de conversa privadas e escolher os membros que podem participar nessas salas. 
	O criador da sala torna-se administrador dessa sala e pode acrescentar outros membros e eleger administradores entre eles.
	Os administradores podem convidar outros membros e outros administradores

### Páginas / CMS

Funcionalidades básicas de CMS: os administradores podem criar páginas HTML estáticas e publicá-las no sítio. 
A página inicial também pode ser configurada desta forma, assim como a política de privacidade, as páginas «Acerca de»... 
As páginas públicas (as que aparecem no menu Páginas mesmo que não tenha iniciado sessão) podem ser criadas e publicadas por qualquer membro administrador. O URL delas tem de começar por '/publish/'
As páginas privadas (as que só aparecem no menu Páginas se tiver iniciado sessão) podem ser criadas e publicadas por qualquer membro administrador. O URL delas tem de começar por '/private/'
As mensagens dos administradores são um tipo específico de página que é apresentada a todos os membros ligados no topo do sítio. O URL delas tem de começar por '/admin-message/'
As outras páginas específicas predefinidas podem ser modificadas por qualquer membro administrador. São acedidas a partir do menu de administração em «Editar páginas» e mostram, respetivamente, a página inicial quando não está ligado (/home/unauthenticated/\<lang>), quando está ligado (/home/authenticated/\<lang>) e a política de privacidade (/about/privacy-policy/\<lang>).

### Tesouros

Este é um local onde pode destacar os tesouros digitais da família, sejam textos, músicas ou vídeos

### Sondagens

Qualquer membro ativo pode criar uma sondagem e qualquer membro ativo pode responder a uma sondagem ativa.
As sondagens têm datas de publicação e de encerramento. Podem conter várias perguntas e as perguntas podem ser:

* perguntas simples de sim/não: marque a caixa de verificação
* texto aberto: introduza o texto formatado que quiser
* data: escolha uma data
* escolhas: escolha uma opção numa lista

### Planeamento de eventos

Como submódulo do módulo de sondagens, qualquer membro ativo pode criar um inquérito de planeamento de eventos para definir quando deve realizar-se um evento. Isto acrescenta ao módulo de sondagens os seguintes tipos de escolhas:

* escolher uma data numa lista fornecida
* escolher várias datas numa lista fornecida

### Anúncios classificados

Qualquer membro ativo pode publicar um anúncio classificado que pode ser visto por todos os outros membros. Se um membro estiver interessado num anúncio, pode enviar uma mensagem ao autor do anúncio, que receberá um e-mail.

### Genealogia

Qualquer membro ativo pode acrescentar pessoas à genealogia do sítio. Pode acrescentar pessoas à genealogia introduzindo os seus dados em formulários ou importando um ficheiro GEDCOM. Pode exportar a genealogia em formato GEDCOM. A genealogia pode ser apresentada como uma árvore dinâmica ou como listas de pessoas ou de famílias.
