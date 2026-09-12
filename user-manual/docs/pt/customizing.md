# Personalizar o seu sítio

## Configurações
Consulte [Configurações](settings.md) para personalizar alterando as configurações.

### Gestão das funcionalidades
Utilizando as configurações, também pode gerir as funcionalidades que serão oferecidas aos membros, conforme explicado em [Gestão das funcionalidades](settings.md/#features-management)

### Preferências de notificação
Os membros podem configurar a frequência das suas notificações por e-mail nas configurações do perfil. Consulte [Funcionalidades - Seguidores e notificações](features.md#seguidores-e-notificacoes) para obter detalhes.

## Criação de páginas
O administrador pode criar ou atualizar páginas estáticas utilizando a funcionalidade «Editar página» na barra de navegação. **Apenas os administradores têm acesso a esta funcionalidade!**

Ao criar uma página, abre-se um formulário que tem de preencher com alguns campos:

* URL: Este campo será utilizado para apresentar a página.
	Existem diferentes categorias de páginas:

	* As páginas «About» (Acerca de), que incluem a política de privacidade descrita abaixo, têm de começar por '/<language-code\>/about/<page-slug\>'. São apresentadas do lado direito da barra de navegação, por baixo de um ícone de ponto de interrogação.
	* As páginas «Home» (Início) são páginas que começam por '/<language-code\>/home/'. Consulte [Páginas iniciais (Home)](#front-or-home-pages) abaixo
	* As páginas «Static» (Estáticas) são páginas que começam por '/publish/'. Podem ter 2 subformas: 

		* /publish/<page-slug\>: o título destas páginas é apresentado diretamente no menu Páginas da barra de navegação.
		* /publish/<menu-name\>/<page-slug\>: São menus pendentes do menu Páginas com o nome «menu-name», e o título de cada página é apresentado na lista pendente por baixo de <menu-name\>.

	* Páginas de mensagem, com um URL que começa por '/admin-message/', consulte [Apresentar uma mensagem de administrador em todas as páginas](#show-an-admin-message-on-all-pages)
	* Qualquer outro URL pode ser incluído como hiperligação noutras páginas, mas não estará acessível a partir da barra de menus.

* Título: é a cadeia de caracteres que será apresentada nos menus.
* Conteúdo: é o conteúdo da página. Pode ser editado utilizando o editor formatado.
* Uma caixa de verificação chamada «Autorizar comentários» é apresentada, mas não é utilizada neste momento.

## Gestão da privacidade
As páginas estáticas (uma por idioma) que descrevem a política de privacidade do sítio são carregadas na base de dados durante a instalação da aplicação.
Estas páginas podem ser personalizadas utilizando a funcionalidade padrão «Editar página» descrita acima.

**AVISO**: Não altere o URL destas páginas! O padrão deste URL é /<language-code\>/about/privacy-policy. Se alterar este padrão, a política de privacidade associada deixará de estar acessível!

## Rodapé personalizado
Defina `SITE_FOOTER` conforme explicado em [Personalização geral](settings.md/#general-customization)

## Páginas iniciais (Home)
O seu sítio precisa de duas páginas iniciais diferentes (também designadas home): 

* a primeira para as pessoas não autenticadas, onde pode explicar o objetivo do seu sítio sem dar demasiados detalhes e nada de privado.
* a segunda é a página para os seus membros depois de iniciarem sessão.
Pode editar estas 2 páginas diretamente a partir da página inicial predefinida ou a partir da lista de páginas no menu.

O URL destas páginas é construído assim: /<language code\>/home/authenticated e /<language code\>/home/unauthenticated.

Versões predefinidas destas duas páginas são carregadas na base de dados no primeiro arranque. 
Se o código de idioma do .env não corresponder a nenhuma das páginas pré-carregadas, é apresentada a versão en-US.

**ATENÇÃO**: Não altere os URLs destas páginas, caso contrário não funcionarão!!!

## Apresentar uma mensagem de administrador em todas as páginas
Os administradores podem criar páginas especiais com um URL que começa por '/admin-message/'. O título desta página só será utilizado na lista de páginas do menu «Editar páginas». O conteúdo destas páginas é apresentado como uma notificação no topo de cada página e pode ser fechado, mas voltará a aparecer em cada nova ligação, enquanto a página existir na base de dados.

Pode criar uma única página com o URL '/admin-message/' ou qualquer número de páginas que comecem todas por '/admin-message/', e cada página será apresentada como uma notificação específica.

## Temas
Para criar o seu próprio tema, é necessário aplicar novos valores às variáveis do Bulma no ficheiro chamado media/public/theme.css (este ficheiro é montado nas imagens docker).

A personalização tem de ter o seguinte formato:

```
:root {
	--bulma-xxx: value;
	--bulma-yyy: value;
	--bulma-zzz: value;
}
```

por exemplo

```
:root {
	--bulma-body-font-size: 16px;
	--bulma-primary-h: 155deg !important;
	--bulma-primary-s: 80% !important;
	--bulma-primary-l: 37% !important;
}
```

alterará o tamanho global das letras do sítio e mudará a cor primária (definida em termos de HSL (matiz, saturação e luminosidade). 
(Pode experimentar as cores HSL em https://hslpicker.com/)

Também pode alterar estas variáveis no âmbito de um componente, mas nesse caso já não é verdadeiramente um tema; consulte os detalhes em [Bulma CSS Variables](https://bulma.io/documentation/features/css-variables/) e [Customizing Bulma with CSS variables](https://bulma.io/documentation/customize/with-css-variables/)

Para conhecer todas as variáveis CSS disponíveis definidas pelo Bulma, consulte o [Bulma CSS File](https://cdn.jsdelivr.net/npm/bulma@1.0.1/css/bulma.css) e experimente-as no seu navegador para ver o efeito.

