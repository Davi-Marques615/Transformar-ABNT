# Compra inicial para publicar o Conversor ABNT

## Conclusão direta

Para colocar o site no ar sem administrar um servidor Linux, eu compraria uma combinação gerenciada de **Render + Supabase + Stripe + Registro.br**. O Render executa o Flask. O Supabase fornece banco PostgreSQL, autenticação e armazenamento. A Stripe cuida da assinatura e repassa os pagamentos para a conta bancária cadastrada. O Registro.br fornece o domínio.

Essa combinação é mais simples do que manter banco, arquivos, autenticação e cobrança em serviços diferentes. Também evita começar com um VPS barato, que exigiria atualizações, firewall, backup, monitoramento e recuperação manual de falhas.

> Nenhuma combinação torna o negócio literalmente “sem precisar fazer nada”. Depois da configuração inicial, cobrança, ativação de planos, falhas de cartão, e-mails e limpeza de arquivos podem ser automáticos. Ainda será necessário acompanhar pagamentos, suporte, impostos, segurança e disponibilidade.

## O que comprar ou ativar

### 1. Domínio `.com.br`

**Fornecedor recomendado:** [Registro.br](https://registro.br/).

O próprio Registro.br informa o valor de **R$ 40,00 por ano** para domínios `.br`.[1] Eu registraria um nome curto, sem hífen e fácil de falar. O domínio é o único item que eu compraria imediatamente, antes de divulgar o produto.

**Custo:** R$ 40,00 por ano.

### 2. Hospedagem da aplicação Flask

**Fornecedor recomendado:** [Render](https://render.com/pricing/), serviço Web Starter.

O plano Starter para Web Service aparece como **US$ 7 por mês**, com 512 MB de RAM e 0,5 CPU.[2] É suficiente para o começo, porque a geração de DOCX é relativamente leve e o site terá poucos usuários simultâneos no lançamento. O Render oferece HTTPS, domínio personalizado e deploy conectado ao repositório.

**Custo de referência:** US$ 7/mês, aproximadamente **R$ 35,91/mês** usando US$ 1 = R$ 5,13 como cotação de planejamento em 22/09/2026. O valor final no cartão pode mudar pelo câmbio e pelo IOF.

**O que configurar:** deploy via Git, variáveis secretas, Gunicorn, health check, domínio, HTTPS e limite de recursos.

### 3. Banco de dados, autenticação e armazenamento

**Fornecedor recomendado:** [Supabase Pro](https://supabase.com/pricing/).

O Supabase Pro aparece como **US$ 25/mês** e inclui banco PostgreSQL dedicado, backups diários, 100.000 usuários ativos mensais, 8 GB de disco por projeto, 250 GB de transferência e 100 GB de armazenamento de arquivos.[3] Ele pode concentrar três necessidades do produto: usuários, assinaturas e documentos gerados.

**Custo de referência:** US$ 25/mês, aproximadamente **R$ 128,25/mês** na cotação de planejamento usada acima.

Eu não escolheria o plano gratuito para uma operação comercial que precisa ficar sempre ativa, porque o plano gratuito pode pausar projetos inativos e não oferece o mesmo nível de backup e suporte. O Pro é o item mais importante para evitar dor de cabeça no banco.

**O que guardar no banco:** usuário, plano, status da assinatura, período atual, quantidade gerada no mês, documentos, data de expiração, eventos de pagamento e logs de auditoria.

**O que guardar no storage:** arquivos DOCX privados, com acesso por links assinados e exclusão automática após a retenção informada ao cliente.

### 4. Pagamentos recorrentes

**Fornecedor recomendado:** [Stripe Payments](https://stripe.com/br/pricing/) + [Stripe Billing](https://stripe.com/br/billing/pricing/).

A Stripe não apresenta uma mensalidade fixa obrigatória no preço padrão. Para o Brasil, a página de preços informa cartão nacional a partir de **3,99% + R$ 0,39** por transação.[4] A página do Billing informa **0,7% do volume no Billing** e, na seção de pagamentos recorrentes, indica **3,99% + R$ 0,50** por cobrança de cartão bem-sucedida.[5] Como há diferenças por produto e contratação, eu reservaria no planejamento a condição mais conservadora de 3,99% + R$ 0,50 + 0,7% até confirmar a tabela no Dashboard.

**Custo fixo:** R$ 0 por mês.

**Custo variável:** aproximadamente 4,69% do valor mais R$ 0,50 por cobrança, na hipótese conservadora acima.

A Stripe deve ativar automaticamente a assinatura após o webhook de pagamento aprovado, suspender ou colocar em carência pagamentos falhos, aceitar cancelamento pelo portal do cliente e repassar o saldo à conta bancária cadastrada. O repasse não significa que não haverá obrigações fiscais: será necessário tratar CNPJ, emissão fiscal e contabilidade.

### 5. E-mails automáticos

**Fornecedor recomendado:** [Resend](https://resend.com/pricing/).

O plano gratuito inclui até **3.000 e-mails por mês**, com limite de 100 por dia.[6] É suficiente para confirmação de cadastro, recuperação de senha, boas-vindas, pagamento aprovado, falha de cobrança e aviso de renovação no início.

**Custo inicial:** R$ 0 por mês.

Eu só passaria ao plano pago quando o volume justificar. A página atual mostra o plano Pro a US$ 20/mês para 50.000 e-mails, mas isso não deve ser comprado no lançamento.[6]

### 6. DNS, proteção e certificados

**Fornecedor recomendado:** [Cloudflare DNS](https://www.cloudflare.com/plans/free/), plano gratuito.

Usaria a Cloudflare para DNS, proteção básica, cache de arquivos estáticos e regras simples de segurança. O certificado HTTPS do Render já resolve o acesso seguro do site, então não compraria certificado separado.

**Custo inicial:** R$ 0 por mês.

### 7. Monitoramento de erros

**Fornecedor recomendado:** [Sentry Developer](https://sentry.io/pricing/), plano gratuito.

O plano gratuito inclui monitoramento de erros e alertas por e-mail, com limite de um usuário.[7] Isso é suficiente para o lançamento, especialmente se a aplicação enviar ao Sentry os erros do Flask e os eventos de geração de documentos.

**Custo inicial:** R$ 0 por mês.

### 8. Repositório e deploy

**Fornecedor recomendado:** [GitHub](https://github.com/pricing/), plano Free para repositório privado.

O código deve ficar versionado em um repositório privado. O Render fará deploy automático somente depois de uma alteração aprovada. O `.env`, chaves da Stripe e credenciais do Supabase nunca devem entrar no GitHub.

**Custo inicial:** R$ 0 por mês.

### 9. Backup adicional

No início, o backup diário do Supabase Pro pode ser a base. Eu também configuraria uma exportação periódica do banco para um armazenamento separado, porque backup e recuperação devem ser testados, não apenas ativados.

**Custo inicial estimado:** R$ 0 a R$ 30 por mês, dependendo do destino escolhido.

Eu não compraria Cloudflare R2 imediatamente se os 100 GB de storage do Supabase forem suficientes. Se o volume de arquivos crescer, o [Cloudflare R2](https://developers.cloudflare.com/r2/pricing/) tem 10 GB-mês, 1 milhão de operações Classe A e 10 milhões de operações Classe B gratuitos por mês; depois cobra US$ 0,015 por GB-mês no storage Standard e não cobra egress.[8]

## Custo total inicial recomendado

A cotação abaixo usa US$ 1 = R$ 5,13 apenas para planejamento. Serviços internacionais serão cobrados em dólar e podem variar no cartão.

| Item | Custo inicial |
|---|---:|
| Domínio Registro.br | R$ 40,00/ano |
| Render Starter | US$ 7/mês ≈ R$ 35,91/mês |
| Supabase Pro | US$ 25/mês ≈ R$ 128,25/mês |
| Stripe | R$ 0 fixo + tarifas por pagamento |
| Resend Free | R$ 0/mês |
| Cloudflare Free | R$ 0/mês |
| Sentry Free | R$ 0/mês |
| GitHub Free | R$ 0/mês |
| **Total mensal fixo** | **aprox. R$ 164,16/mês** |
| **Primeiro mês incluindo domínio** | **aprox. R$ 204,16** |
| **12 meses incluindo domínio** | **aprox. R$ 2.009,92** |

Esse valor é de infraestrutura e não inclui desenvolvimento, contador, imposto, anúncios, suporte ou taxa de pagamento. Eu reservaria uma margem de segurança de 10% a 20% para variação cambial e consumo excedente. Assim, o orçamento de tecnologia ficaria em torno de **R$ 180 a R$ 200 por mês**, mais as tarifas das vendas.

## Alternativa mais barata

Existe uma alternativa com custo fixo menor: usar **Railway Hobby** para a aplicação e PostgreSQL no mesmo provedor. O plano Hobby aparece como US$ 5/mês com US$ 5 de uso incluído, mas o consumo é medido por CPU, memória, volume e tráfego.[9]

| Abordagem | Custo de referência | Vantagem | Desvantagem |
|---|---:|---|---|
| **Render + Supabase Pro** | cerca de R$ 164,16/mês + domínio anual | Mais simples de administrar; autenticação, banco, storage e backups separados | Custa mais no início |
| **Railway Hobby + PostgreSQL** | a partir de US$ 5/mês, mais consumo | Mais barato e tudo no mesmo painel | Cobrança variável e menos confortável para separar storage, auth e recuperação |
| **VPS próprio** | geralmente mais barato em dinheiro | Controle total e baixo custo nominal | Exige administrar segurança, banco, backup, atualizações e falhas |

Para o seu caso, eu escolheria **Render + Supabase Pro**, mesmo não sendo a opção de menor preço. A diferença mensal compra simplicidade e reduz o risco de uma falha no banco ou de um arquivo de usuário ficar exposto.

## Como deixar tudo automático

A automação precisa ser implementada antes da divulgação do site. O fluxo deve ser:

1. O visitante cria uma conta.
2. Escolhe o plano mensal ou anual.
3. A Stripe processa a cobrança.
4. Um webhook assinado informa o resultado ao sistema.
5. O sistema ativa o plano sem intervenção manual.
6. Antes de gerar, o sistema verifica a quantidade mensal do Básico.
7. O sistema gera o DOCX e salva o arquivo privado.
8. O cliente baixa pelo próprio painel.
9. O sistema envia e-mails automáticos.
10. Uma rotina remove arquivos vencidos.
11. Pagamentos falhos entram em carência e seguem a regra definida.
12. O painel administrativo mostra usuários, planos, gerações, falhas e receita.

A assinatura anual deve ser cobrada uma vez no início do período. O plano não deve depender de o administrador liberar manualmente o acesso.

## Preços dos seus planos

Eu acho que **R$ 24,90 no Pro é aceitável para o lançamento**, mas eu trataria como preço de entrada. O custo de geração é baixo, então o preço pode funcionar. O risco é o suporte: se o cliente esperar revisão completa do TCC, correção de ABNT ou atendimento individual, R$ 24,90 ficará baixo.

Minha tabela inicial seria:

| Plano | Mensal | Anual com dois meses grátis | Equivalente mensal no anual |
|---|---:|---:|---:|
| **Básico — 5 documentos** | **R$ 14,90** | **R$ 149,00/ano** | R$ 12,42 |
| **Pro — ilimitado** | **R$ 24,90** | **R$ 249,00/ano** | R$ 20,75 |

Eu usaria essa tabela somente se o produto for bem automatizado e o suporte for limitado ao funcionamento da plataforma. Se houver suporte humano frequente, eu preferiria R$ 19,90 no Básico e R$ 34,90 ou R$ 39,90 no Pro.

Para proteger a margem, o Pro deve incluir “documentos ilimitados para uso pessoal, sujeito à política de uso justo”. A regra não deve esconder limites artificiais, mas precisa impedir scripts, contas compartilhadas e geração automatizada em massa.

## O que ainda precisa ser desenvolvido

Comprar os serviços não coloca o SaaS automaticamente no ar. O código atual ainda precisa receber autenticação, banco, integração da Stripe, webhooks, controle de quota, histórico, storage privado, recuperação de senha, e-mails, painel administrativo, política de exclusão, rate limiting, logs, testes e configuração segura de produção.

O custo de infraestrutura acima é baixo. O maior investimento é transformar o gerador atual em um produto seguro. Eu faria primeiro um piloto pago, com os quatro preços definidos, e só depois adicionaria recursos mais complexos.

## Checklist de compra

- [ ] Registrar o domínio no Registro.br.
- [ ] Criar conta no GitHub.
- [ ] Criar conta no Render e contratar o Web Starter.
- [ ] Criar organização no Supabase e contratar o Pro.
- [ ] Criar conta Stripe e validar dados bancários e fiscais.
- [ ] Criar quatro preços na Stripe: Básico mensal, Básico anual, Pro mensal e Pro anual.
- [ ] Criar conta gratuita no Resend e verificar o domínio de envio.
- [ ] Criar conta gratuita no Sentry.
- [ ] Configurar Cloudflare DNS.
- [ ] Implementar e testar os webhooks e a recuperação de pagamento.
- [ ] Fazer testes de cadastro, pagamento, cancelamento, falha e renovação.
- [ ] Publicar termos de uso, política de privacidade e contato.

## Referências

[1]: https://registro.br/ "Registro.br — registro de domínio por R$ 40,00 por ano"
[2]: https://render.com/pricing/ "Render — preços de hospedagem e serviços"
[3]: https://supabase.com/pricing "Supabase — preços de banco, autenticação e storage"
[4]: https://stripe.com/br/pricing/ "Stripe Brasil — preços de pagamentos"
[5]: https://stripe.com/br/billing/pricing/ "Stripe Billing Brasil — preços de assinaturas"
[6]: https://resend.com/pricing/ "Resend — preços de e-mail transacional"
[7]: https://sentry.io/pricing/ "Sentry — preços de monitoramento de erros"
[8]: https://developers.cloudflare.com/r2/pricing/ "Cloudflare R2 — preços de armazenamento"
[9]: https://railway.com/pricing "Railway — preços de hospedagem e uso de recursos"
