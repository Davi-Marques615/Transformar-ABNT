# Passo a passo para colocar o Conversor ABNT em produção

## O que foi programado

O projeto agora possui cadastro, login, sessão segura, proteção CSRF, página de planos, conta do usuário, controle de cinco gerações mensais no plano Básico, plano Pro sem limite mensal fixo, checkout Stripe preparado, webhook idempotente para atualização de assinatura, limites de upload e geração do DOCX em diretório temporário.

O DOCX não fica salvo depois da resposta. O servidor lê o arquivo gerado para a resposta HTTP e envia os bytes ao navegador. Em seguida, a pasta temporária é removida. O banco guarda somente o usuário, o plano, o status da assinatura e o contador mensal.

Os testes executados foram:

- compilação de `app.py`, `gerador_abnt.py` e scripts de teste;
- carregamento das rotas `/`, `/planos`, `/entrar`, `/cadastro` e `/health`;
- criação de conta e abertura da página de conta;
- geração real de um DOCX;
- verificação do formato DOCX;
- verificação de que o documento não ficou na pasta do projeto.

## Importante sobre o banco

A versão implementada usa SQLite. Isso é adequado para desenvolvimento e um primeiro piloto com **uma única instância** e disco persistente. O arquivo `render.yaml` já configura um disco persistente de 1 GB no Render em `/var/data`.

Antes de escalar para várias instâncias ou exigir alta disponibilidade, o banco deve ser migrado para PostgreSQL. Não se deve executar esta versão com SQLite em um armazenamento efêmero, porque usuários, assinaturas e quotas seriam perdidos quando o serviço fosse recriado.

## Etapa 1 — preparar o código

1. Crie um repositório privado no [GitHub](https://github.com/).
2. Coloque nele os arquivos desta pasta.
3. Não envie `.env`, banco `.sqlite3`, arquivos `.docx` ou a pasta `output`.
4. Faça um primeiro commit e confirme que o repositório está privado.

## Etapa 2 — criar a hospedagem

1. Crie sua conta no [Render](https://render.com/).
2. Conecte o GitHub.
3. Crie um Blueprint usando o arquivo `render.yaml` ou crie manualmente um Web Service.
4. Use o plano Starter.
5. Confirme o disco persistente de 1 GB montado em `/var/data`.
6. O comando de build é `pip install -r requirements.txt`.
7. O comando de início é `gunicorn --bind 0.0.0.0:$PORT app:app`.
8. Verifique que `/health` responde com status 200.

O domínio temporário do Render serve para teste. Depois, conecte o domínio próprio.

## Etapa 3 — domínio e DNS

1. Registre o domínio no [Registro.br](https://registro.br/).
2. No Render, abra a área de domínio personalizado.
3. Adicione o domínio.
4. Copie os registros DNS solicitados.
5. No Registro.br ou no provedor DNS, crie os registros solicitados.
6. Aguarde a propagação.
7. Confirme que o HTTPS está ativo.

## Etapa 4 — configurar as variáveis do Render

No painel do Render, abra Environment e preencha:

- `SECRET_KEY`: use a chave gerada pelo próprio Render ou uma chave longa aleatória;
- `COOKIE_SECURE`: `1`;
- `FLASK_DEBUG`: `0`;
- `ALLOW_UNPAID_GENERATION`: `0`;
- `DATABASE_PATH`: `/var/data/abnt.sqlite3`.

Não coloque chaves de teste em produção. A chave secreta e as chaves Stripe devem ser adicionadas somente no painel do Render, nunca no GitHub.

## Etapa 5 — criar os produtos Stripe

1. Abra uma conta no [Stripe](https://dashboard.stripe.com/register).
2. Complete os dados da empresa, identidade, conta bancária e informações fiscais solicitadas pela Stripe.
3. Use o modo de teste para validar tudo.
4. Crie quatro preços recorrentes:
   - Básico mensal: R$ 14,90;
   - Básico anual: R$ 149,00;
   - Pro mensal: R$ 24,90;
   - Pro anual: R$ 249,00.
5. Copie os quatro IDs `price_...` para estas variáveis no Render:
   - `STRIPE_PRICE_BASIC_MONTHLY`;
   - `STRIPE_PRICE_BASIC_ANNUAL`;
   - `STRIPE_PRICE_PRO_MONTHLY`;
   - `STRIPE_PRICE_PRO_ANNUAL`.
6. Copie a chave secreta de teste para `STRIPE_SECRET_KEY` durante os testes.

Também é possível usar diretamente os IDs de produto `prod_...` enviados pelo proprietário. O código consulta o preço padrão de cada produto. Nesse caso, preencha `STRIPE_PRODUCT_BASIC_MONTHLY`, `STRIPE_PRODUCT_BASIC_ANNUAL`, `STRIPE_PRODUCT_PRO_MONTHLY` e `STRIPE_PRODUCT_PRO_ANNUAL`, e deixe as variáveis `STRIPE_PRICE_...` vazias.

## Etapa 6 — configurar o webhook Stripe

1. No Stripe, abra Developers > Webhooks.
2. Crie um endpoint com a URL:
   `https://SEU-DOMINIO.com.br/stripe/webhook`
3. Selecione pelo menos estes eventos:
   - `checkout.session.completed`;
   - `customer.subscription.updated`;
   - `customer.subscription.deleted`;
   - `invoice.paid`;
   - `invoice.payment_failed`.
4. Copie o signing secret `whsec_...` para `STRIPE_WEBHOOK_SECRET` no Render.
5. Faça um checkout de teste.
6. Confirme que a conta muda para o plano ativo.
7. Confirme que a geração fica liberada.
8. Teste cancelamento e falha de pagamento.

Depois de testar, troque para o modo Live, crie os quatro preços no modo Live e substitua as chaves e os IDs no Render. As chaves de teste e Live são diferentes.

## Etapa 6.1 — portal de assinatura

No Stripe, abra Billing > Customer portal e ative o portal para clientes. Permita atualização de forma de pagamento, cancelamento e visualização de faturas. O botão **Gerenciar assinatura** da página Minha conta abrirá esse portal. O código usa o `stripe_customer_id` salvo pelo webhook; por isso é necessário concluir pelo menos um checkout e configurar o webhook antes de testar esse botão.

## Etapa 7 — testar antes de divulgar

Faça os testes abaixo em produção:

1. Criar conta com e-mail válido.
2. Tentar gerar sem plano: deve bloquear.
3. Fazer pagamento de teste: deve liberar.
4. Gerar um documento no computador.
5. Abrir o DOCX no Word ou LibreOffice.
6. Gerar cinco documentos no Básico.
7. Confirmar que o sexto é bloqueado.
8. Confirmar que nenhum DOCX aparece na pasta do servidor.
9. Testar geração pelo celular.
10. Testar pagamento anual.
11. Testar cancelamento.
12. Testar e-mail e senha incorretos.
13. Testar arquivo de imagem acima do limite.
14. Testar uma requisição sem CSRF.

## O que você precisa fazer pessoalmente

Eu não posso abrir ou concluir, em seu nome, contas financeiras, validação de identidade, cadastro bancário, contratação de serviços, aceite de termos, configuração de domínio ou publicação do negócio. Essas etapas exigem seus dados, seus meios de pagamento e sua responsabilidade legal.

Você precisará:

- criar e validar a conta Stripe;
- informar sua conta bancária e dados fiscais;
- decidir se vai operar como pessoa física ou empresa com orientação contábil;
- comprar o domínio;
- criar e conectar o GitHub e Render;
- inserir as chaves secretas nos painéis;
- testar os pagamentos reais;
- publicar termos de uso e política de privacidade;
- acompanhar suporte, impostos, chargebacks e falhas de pagamento.

## Etapa 8 — configurar o Resend

O cadastro agora chama a API do Resend para enviar um e-mail de boas-vindas. A integração usa a API REST diretamente, então não foi necessário adicionar um SDK JavaScript a um projeto Flask. Se o Resend estiver sem configuração ou indisponível, a conta ainda é criada normalmente e o erro fica apenas no log.

1. Abra ou crie sua conta no [Resend](https://resend.com/).
2. Crie uma API key com permissão de envio.
3. No Render, abra Environment e preencha `RESEND_API_KEY` com a sua chave real, que começa com `re_`.
4. Não coloque essa chave no GitHub, no HTML, no JavaScript do navegador ou em mensagens públicas.
5. Para teste, `RESEND_FROM_EMAIL=onboarding@resend.dev` pode ser usado conforme as limitações da conta Resend.
6. Para produção, verifique seu próprio domínio no Resend e use um remetente como `contato@seudominio.com.br`.
7. Faça um cadastro de teste e confirme o e-mail de boas-vindas.

No arquivo `.env.example`, o valor `re_substitua_pela_sua_chave_real` é apenas um marcador. Você precisa substituí-lo pela sua chave real no painel do Render ou no arquivo `.env` local. A chave enviada durante a conversa não foi gravada no código-fonte.

## Limite atual antes de chamar de “100% automático”

A cobrança e a ativação podem ser automáticas depois que as contas e os webhooks forem configurados. Ainda faltam, para uma operação comercial mais madura, recuperação de senha por e-mail, envio de e-mails transacionais, painel administrativo, PostgreSQL e rotina de backup testada. O fluxo atual já é uma base funcional de SaaS e piloto pago, mas não deve ser tratado como produto final de alta escala sem essas etapas.

## Arquivos principais adicionados ou alterados

- `app.py`: autenticação, planos, quota, Stripe e geração temporária;
- `templates/auth.html`: cadastro e login;
- `templates/plans.html`: preços e checkout;
- `templates/account.html`: status da conta;
- `static/saas.css`: estilos das páginas SaaS;
- `.env.example`: variáveis necessárias;
- `render.yaml`: deploy no Render com disco persistente;
- `.gitignore`: proteção contra segredos, banco e documentos;
- `test_smoke.py` e `test_generation.py`: testes locais.
