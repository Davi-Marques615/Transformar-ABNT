# Análise para publicar o Conversor ABNT como SaaS

## Resumo executivo

**Sim, pode dar lucro**, porque o custo marginal de gerar um arquivo DOCX é baixo. O risco principal não está no processamento do documento, mas em aquisição de clientes, suporte, qualidade das normas ABNT, inadimplência, segurança e manutenção do sistema.

Minha recomendação inicial seria lançar com preços simples:

| Plano | Limite | Mensal | Anual sugerido |
|---|---:|---:|---:|
| **Básico** | 5 documentos por mês | **R$ 19,90/mês** | **R$ 199/ano** |
| **Pro** | Documentos ilimitados, sujeito a uso justo e antifraude | **R$ 39,90/mês** | **R$ 399/ano** |

O plano anual equivale a aproximadamente dois meses grátis. Eu não começaria abaixo de R$ 14,90 no Básico e R$ 29,90 no Pro, porque a tarifa fixa de pagamento pesa bastante em assinaturas baratas e ainda existem impostos, suporte e divulgação.

## 1. O que o produto atual já faz

O código atual é um protótipo funcional em Flask. Ele recebe um formulário e gera arquivos DOCX com vários elementos acadêmicos: capa, folha de rosto, folha de aprovação, dedicatória, agradecimentos, epígrafe, resumo, abstract, sumário, seções numeradas, imagens, referências, glossário, apêndice e anexo.

Isso é uma boa base para o produto. Entretanto, a aplicação ainda é essencialmente local e não possui:

- cadastro, login e recuperação de senha;
- banco de dados para usuários, assinaturas e documentos;
- integração de cobrança recorrente;
- controle de cinco gerações mensais ou de plano Pro;
- histórico dos arquivos do usuário;
- armazenamento privado e expiração automática dos arquivos;
- painel administrativo;
- confirmação de e-mail;
- termos de uso, política de privacidade e fluxo de cancelamento;
- proteção contra abuso, limites de tamanho e rate limiting;
- configuração de produção segura.

Também há pontos que precisam ser corrigidos antes de publicar: o `SECRET_KEY` está fixo no código, o servidor inicia com `debug=True` quando executado diretamente e os arquivos são gravados em uma pasta local do servidor. Em produção, essas escolhas não são adequadas.

## 2. Preços que eu praticaria

### Plano Básico — R$ 19,90 por mês

Inclui cinco documentos gerados por ciclo mensal, edição dos dados, download do DOCX e histórico dos últimos documentos. É um preço baixo o suficiente para estudantes testarem, mas não tão baixo a ponto de a tarifa fixa consumir uma parcela exagerada da receita.

### Plano Pro — R$ 39,90 por mês

Inclui geração ilimitada para uso individual, histórico maior, prioridade de processamento e recursos avançados que forem adicionados. A palavra “ilimitado” deve vir acompanhada de uma política de uso justo, tamanho máximo de arquivo, limite de requisições por minuto e bloqueio de automação abusiva. Isso não reduz o benefício legítimo do plano; evita que alguém use o serviço como uma API pública ou gere milhares de arquivos automaticamente.

### Plano anual

Eu cobraria R$ 199 no Básico e R$ 399 no Pro. O cliente recebe cerca de dois meses de desconto, enquanto você melhora o caixa e reduz a chance de cancelamento mensal. No lançamento, também poderia haver uma oferta de fundador por tempo limitado, mas eu evitaria manter desconto permanente.

## 3. A conta da margem

A Stripe informa, na página de preços do Brasil, tarifa de cartão nacional de **3,99% mais uma tarifa fixa por transação**. Na página específica do Billing, a cobrança recorrente aparece com **0,7% do volume no Billing** e a cobrança de cartão indicada é **3,99% mais R$ 0,50**. As condições devem ser confirmadas no momento da contratação, porque podem variar por produto, método de pagamento e volume.

Usando uma conta conservadora com 3,99% + R$ 0,50 e 0,7% de Billing, antes de impostos:

| Venda | Receita bruta | Estimativa de tarifas | Sobra antes de impostos e suporte |
|---|---:|---:|---:|
| Básico mensal | R$ 19,90 | cerca de R$ 1,43 | cerca de R$ 18,47 |
| Pro mensal | R$ 39,90 | cerca de R$ 2,37 | cerca de R$ 37,53 |
| Básico anual | R$ 199,00 | cerca de R$ 9,83 | cerca de R$ 189,17 |
| Pro anual | R$ 399,00 | cerca de R$ 19,21 | cerca de R$ 379,79 |

Ainda é necessário descontar impostos, contabilidade, anúncios, atendimento, reembolsos e eventuais perdas por chargeback. Para uma empresa pequena no Simples Nacional, a alíquota efetiva precisa ser confirmada com um contador; para planejamento preliminar, reservar algo em torno de 6% ou mais é mais prudente do que assumir imposto zero.

Com uma mistura de clientes e um custo fixo operacional de aproximadamente R$ 500 por mês, o ponto de equilíbrio técnico poderia ficar perto de **15 clientes Pro**, ou **29 clientes Básico**, sem contar um orçamento relevante de anúncios. Com marketing pago, o número necessário sobe conforme o custo para adquirir cada cliente.

Exemplo de receita bruta mensal:

| Base de assinantes | Composição | Receita bruta mensal |
|---:|---|---:|
| 50 | 35 Básico + 15 Pro | R$ 1.294,00 |
| 100 | 70 Básico + 30 Pro | R$ 2.793,00 |
| 300 | 210 Básico + 90 Pro | R$ 8.379,00 |
| 1.000 | 700 Básico + 300 Pro | R$ 27.930,00 |

Esses valores são faturamento, não lucro. O negócio se torna interessante quando consegue manter cancelamento baixo, atendimento eficiente e aquisição orgânica por busca, TikTok, Instagram, YouTube, indicação e parcerias com estudantes ou cursos.

## 4. Quanto custaria colocar no ar

### Infraestrutura mensal inicial

Uma composição gerenciada, adequada para começar, poderia ser:

| Item | Estimativa inicial |
|---|---:|
| Domínio `.com.br` | cerca de R$ 40 por ano, conforme o Registro.br |
| Hospedagem web gerenciada | cerca de US$ 20/mês em um plano Pro, ou alternativa equivalente |
| Banco de dados, autenticação e storage | cerca de US$ 25/mês em um plano Pro quando o gratuito deixar de ser suficiente |
| E-mails transacionais | gratuito no começo dentro do limite; serviço pago quando crescer |
| Pagamento | sem mensalidade fixa em muitos cenários, mas com tarifa por transação |
| Monitoramento e backups extras | R$ 0 a R$ 150/mês no início |
| Contabilidade e obrigações da empresa | aproximadamente R$ 300 a R$ 800/mês, dependendo da cidade e do contador |

Como ordem de grandeza, eu reservaria **R$ 250 a R$ 500 por mês somente para tecnologia** no início, usando dólar de planejamento aproximado e sem tráfego elevado. Com contabilidade, serviços administrativos e pequenas ferramentas, um orçamento realista fica em **R$ 600 a R$ 1.300 por mês**, antes de anúncios.

É possível reduzir a infraestrutura usando um VPS único, mas isso aumenta a responsabilidade de configurar atualizações, backups, segurança, monitoramento e recuperação de falhas. Para uma primeira versão comercial, eu priorizaria serviços gerenciados.

### Custo de desenvolvimento

Como o gerador já existe, eu separaria em três níveis:

| Escopo | O que inclui | Estimativa de implantação |
|---|---|---:|
| Piloto pago | login, planos, limite, checkout, webhooks, deploy e correções básicas | **R$ 5 mil a R$ 12 mil** |
| SaaS comercial | tudo acima + painel, histórico, storage privado, e-mails, backups, logs, testes e LGPD | **R$ 12 mil a R$ 30 mil** |
| Produto mais robusto | equipe/admin completo, analytics, recuperação de cobrança, antifraude, suporte e refinamento de UX | **R$ 30 mil a R$ 60 mil ou mais** |

Se o próprio dono desenvolver, o desembolso financeiro pode ser menor, mas o custo aparece em tempo. Eu começaria pelo piloto pago, validaria se as pessoas realmente pagam e só depois investiria em recursos avançados.

## 5. Como deixar o fluxo automático

A arquitetura que eu usaria seria:

1. **Site e aplicação:** manter o gerador Python/Flask, rodando com Gunicorn, atrás de HTTPS e proxy gerenciado.
2. **Contas:** cadastro por e-mail, senha armazenada com hash, confirmação de e-mail, recuperação de senha e sessões seguras.
3. **Banco:** tabelas para usuários, planos, assinaturas, documentos, contagem mensal, status de pagamento e logs.
4. **Checkout:** criar os dois preços mensais e os dois preços anuais no provedor de pagamentos.
5. **Webhooks:** receber eventos de assinatura criada, pagamento aprovado, pagamento recusado, cancelamento e período de carência. O webhook deve ser idempotente para não duplicar créditos ou bloquear clientes por engano.
6. **Entitlements:** antes de gerar, verificar o plano ativo e a quantidade usada no mês. O Básico bloqueia após cinco gerações; o Pro libera a geração, mas continua sujeito a rate limiting e uso justo.
7. **Geração:** enviar a tarefa para uma fila, gerar o DOCX fora da requisição quando necessário, salvar o arquivo em storage privado e oferecer download autenticado.
8. **Limpeza automática:** excluir arquivos antigos conforme a política de retenção, por exemplo 30 ou 90 dias, informada claramente ao usuário.
9. **E-mails:** enviar confirmação, boas-vindas, pagamento aprovado, falha de pagamento, aviso de renovação e recuperação de senha.
10. **Operação:** backups, logs, alertas de erro, monitoramento de disponibilidade, limite de gastos e painel para consultar assinaturas e gerações.
11. **Conformidade:** termos de uso, política de privacidade, canal de contato, política de cancelamento/reembolso e revisão com contador ou advogado sobre emissão fiscal e LGPD.

O fluxo ideal para o cliente seria: criar conta, escolher plano, pagar no checkout, voltar automaticamente ao sistema, preencher o formulário, clicar em gerar e baixar o documento. Se um pagamento falhar, o sistema deve avisar, tentar a recuperação automática e suspender o benefício apenas após a regra de carência definida.

## 6. Minha recomendação prática

Eu faria um lançamento em duas etapas. Primeiro, colocaria no ar uma versão mínima com o Básico de R$ 19,90 e o Pro de R$ 39,90, sem tentar construir um editor completo. Mediria número de cadastros, porcentagem que gera o primeiro documento, conversão para pagamento, documentos por cliente, chamados de suporte e cancelamentos.

Depois de 30 a 60 dias, eu ajustaria o preço conforme o comportamento real. Se o Pro tiver uso intenso ou suporte elevado, subiria para R$ 49,90 antes de adicionar muitas funcionalidades. Se muita gente usar apenas uma vez, criaria também uma compra avulsa de teste, por exemplo R$ 9,90, sem deixar isso substituir a assinatura.

**Conclusão:** o produto tem potencial de lucro, mas não deve ser vendido apenas como “um formulário que gera Word”. A proposta comercial precisa ser “gerar trabalhos acadêmicos organizados no padrão ABNT com rapidez, histórico e segurança”. O primeiro objetivo deveria ser alcançar os primeiros 50 clientes pagantes e validar retenção; a escala deve vir somente depois dessa validação.

## Fontes consultadas

- [Stripe — preços no Brasil](https://stripe.com/br/pricing)
- [Stripe Billing — preços de assinaturas](https://stripe.com/br/billing/pricing)
- [Supabase — preços](https://supabase.com/pricing)
- [Vercel — preços](https://vercel.com/pricing)
- [Resend — preços de e-mail transacional](https://resend.com/pricing)
- [Registro.br — registro de domínios](https://registro.br/)

*As estimativas são planejamento, não orçamento comercial. Tarifas, câmbio, impostos e disponibilidade de recursos devem ser confirmados antes do lançamento.*
