(function () {
    "use strict";

    const form = document.querySelector(".abnt-form");
    const autoresContainer = document.getElementById("autores-container");
    const secoesContainer = document.getElementById("secoes-container");
    const adicionarAutorButton = document.getElementById("adicionar-autor");
    const adicionarSecaoButton = document.getElementById("adicionar-secao");
    const anoInput = document.getElementById("ano");
    const submitButton = form ? form.querySelector('button[type="submit"]') : null;
    const STORAGE_KEY = "convertor_abnt_rascunho_v2";

    if (!form) {
        return;
    }

    adicionarAutorButton?.addEventListener("click", adicionarAutor);
    adicionarSecaoButton?.addEventListener("click", adicionarSecao);
    secoesContainer?.addEventListener("click", manipularAcaoSecao);
    anoInput?.addEventListener("input", limitarAnoAQuatroDigitos);
    form.addEventListener("submit", validarFormulario);
    form.addEventListener("reset", restaurarFormulario);
    form.addEventListener("input", salvarRascunho);
    form.addEventListener("change", salvarRascunho);
    restaurarRascunho();

    // Adicionar autor
    function adicionarAutor(event) {
        event.preventDefault();
        const totalAutores = autoresContainer.querySelectorAll("input[name^='autor_']").length + 1;
        const field = document.createElement("label");
        const inputId = `autor_${totalAutores}`;

        field.className = "field author-field";
        field.setAttribute("for", inputId);
        field.innerHTML = `
            <span>Autor ${totalAutores}</span>
            <div class="author-control">
                <input type="text" id="${inputId}" name="${inputId}" required>
                <button type="button" class="secondary-button remove-author" aria-label="Remover autor ${totalAutores}">Remover</button>
            </div>
        `;

        const removeButton = field.querySelector(".remove-author");
        removeButton.addEventListener("click", function (e) {
            e.preventDefault();
            field.remove();
            renumerarAutores();
            mostrarNotificacao("Autor removido com sucesso", "success");
        });

        autoresContainer.appendChild(field);
        field.querySelector("input").focus();
        mostrarNotificacao("Novo autor adicionado", "success");
    }

    // Adicionar seção
    function adicionarSecao(event) {
        event.preventDefault();
        const totalSecoes = secoesContainer.querySelectorAll(".work-section").length + 1;
        const fieldset = document.createElement("fieldset");
        const sectionId = totalSecoes;

        fieldset.className = "work-section";
        fieldset.setAttribute("data-section-index", sectionId);
        fieldset.innerHTML = `
            <legend>Seção ${sectionId}</legend>
            <div class="field-grid">
                <label class="field field-full" for="secao_titulo_${sectionId}">
                    <span class="label-with-help">
                        Título da seção
                        <button type="button" class="tooltip-button" aria-label="Ajuda sobre título da seção" data-tooltip="Nome da parte do trabalho, como Introdução, Desenvolvimento, Metodologia ou Considerações finais.">?</button>
                    </span>
                    <input type="text" id="secao_titulo_${sectionId}" name="secao_titulo" required>
                </label>

                <label class="field" for="secao_nivel_${sectionId}">
                    <span class="label-with-help">
                        Nível da seção
                        <button type="button" class="tooltip-button" aria-label="Ajuda sobre nível da seção" data-tooltip="Use seção principal para capítulos como 1, 2 e 3. Use subseções para itens como 1.1, 1.1.1 e seguintes.">?</button>
                    </span>
                    <select id="secao_nivel_${sectionId}" name="secao_nivel">
                        <option value="1">Seção principal</option>
                        <option value="2">Subseção</option>
                        <option value="3">Subseção terciária</option>
                        <option value="4">Subseção quaternária</option>
                        <option value="5">Subseção quinária</option>
                    </select>
                </label>

                <label class="field field-full" for="secao_conteudo_${sectionId}">
                    <span class="label-with-help">
                        Texto da seção
                        <button type="button" class="tooltip-button" aria-label="Ajuda sobre texto da seção" data-tooltip="Conteúdo dessa parte do trabalho. Pode ficar em branco se você quiser criar apenas o título da seção.">?</button>
                    </span>
                    <textarea id="secao_conteudo_${sectionId}" name="secao_conteudo" rows="10"></textarea>
                </label>

                <div class="field field-full image-settings-group">
                    <div class="image-settings-heading"><span>Imagens da seção (até 2)</span><small>Configurações ABNT: posição, largura, título/legenda e fonte.</small></div>
                    <div class="section-images-grid">${criarSlotImagem(sectionId, 1)}</div>
                </div>

                <div class="field field-full work-section-actions">
                    <button type="button" class="secondary-button duplicate-section" aria-label="Duplicar seção ${sectionId}">Duplicar seção</button>
                    <button type="button" class="secondary-button remove-section" aria-label="Remover seção ${sectionId}">Remover seção</button>
                </div>
            </div>
        `;

        secoesContainer.appendChild(fieldset);
        fieldset.querySelector("input").focus();
        mostrarNotificacao("Nova seção adicionada", "success");
        salvarRascunho();
    }

    function criarSlotImagem(sectionId, slot) {
        const prefixo = `secao_imagem_${sectionId}_${slot}`;
        return `
            <div class="image-slot">
                <strong>Imagem ${slot}</strong>
                <input type="file" id="${prefixo}" name="${prefixo}" accept=".png,.jpg,.jpeg,.gif,.bmp,.tif,.tiff">
                <div class="image-options">
                    <label class="field"><span>Posição</span><select name="${prefixo}_alinhamento"><option value="center">Centralizada</option><option value="left">À esquerda</option><option value="right">À direita</option></select></label>
                    <label class="field"><span>Largura (mm)</span><input type="number" name="${prefixo}_largura" min="20" max="170" value="100"></label>
                    <label class="field"><span>Título/legenda</span><input type="text" name="${prefixo}_titulo" placeholder="Ex.: Figura ${slot} – ..."></label>
                    <label class="field"><span>Fonte</span><input type="text" name="${prefixo}_fonte" placeholder="Ex.: Elaborado pelo autor (2026)"></label>
                </div>
            </div>`;
    }

    function manipularAcaoSecao(event) {
        if (event.target.closest(".duplicate-section")) {
            duplicarSecao(event);
            return;
        }
        if (event.target.closest(".remove-section")) {
            removerSecao(event);
        }
    }

    function duplicarSecao(event) {
        event.preventDefault();
        const original = event.target.closest(".work-section");
        if (!original) return;

        const copia = original.cloneNode(true);
        copia.querySelectorAll("input[type='file']").forEach(function (campo) {
            campo.value = "";
        });
        copia.querySelectorAll("[aria-invalid='true']").forEach(function (campo) {
            campo.removeAttribute("aria-invalid");
            campo.style.borderColor = "";
        });
        secoesContainer.appendChild(copia);
        renumerarSecoes();
        salvarRascunho();
        const titulo = copia.querySelector("input[name='secao_titulo']");
        titulo?.focus();
        mostrarNotificacao("Seção duplicada. Se houver imagem, selecione o arquivo novamente.", "success");
    }

    function removerSecao(event) {
        const removeButton = event.target.closest(".remove-section");
        if (!removeButton) {
            return;
        }

        event.preventDefault();
        const fieldset = removeButton.closest(".work-section");
        if (secoesContainer.querySelectorAll(".work-section").length > 1 && fieldset) {
            fieldset.remove();
            renumerarSecoes();
            mostrarNotificacao("Seção removida com sucesso", "success");
            salvarRascunho();
            return;
        }

        mostrarNotificacao("Você deve manter pelo menos uma seção", "error");
    }

    // Renumerar autores
    function renumerarAutores() {
        autoresContainer.querySelectorAll(".field").forEach(function (field, index) {
            const numero = index + 1;
            const input = field.querySelector("input");
            const label = field.querySelector("span");
            const removeButton = field.querySelector(".remove-author");
            const inputId = `autor_${numero}`;

            field.setAttribute("for", inputId);
            label.textContent = `Autor ${numero}`;
            input.id = inputId;
            input.name = inputId;

            if (removeButton) {
                removeButton.setAttribute("aria-label", `Remover autor ${numero}`);
            }
        });
    }

    // Renumerar seções
    function renumerarSecoes() {
        secoesContainer.querySelectorAll(".work-section").forEach(function (fieldset, index) {
            const numero = index + 1;
            const legend = fieldset.querySelector("legend");
            const tituloInput = fieldset.querySelector("input[name='secao_titulo']");
            const nivelSelect = fieldset.querySelector("select[name='secao_nivel']");
            const conteudoTextarea = fieldset.querySelector("textarea[name='secao_conteudo']");
            const removeButton = fieldset.querySelector(".remove-section");
            const duplicateButton = fieldset.querySelector(".duplicate-section");

            fieldset.setAttribute("data-section-index", numero);
            legend.textContent = `Seção ${numero}`;

            if (tituloInput) {
                tituloInput.id = `secao_titulo_${numero}`;
            }
            if (nivelSelect) {
                nivelSelect.id = `secao_nivel_${numero}`;
            }
            if (conteudoTextarea) {
                conteudoTextarea.id = `secao_conteudo_${numero}`;
            }
            fieldset.querySelectorAll(".image-slot").forEach(function (slot, slotIndex) {
                const slotNumero = slotIndex + 1;
                const prefixo = `secao_imagem_${numero}_${slotNumero}`;
                const arquivo = slot.querySelector("input[type='file']");
                if (arquivo) { arquivo.id = prefixo; arquivo.name = prefixo; }
                slot.querySelectorAll("select, input:not([type='file'])").forEach(function (campo) {
                    const sufixo = campo.name.split("_").slice(-1)[0];
                    if (["alinhamento", "largura", "titulo", "fonte"].includes(sufixo)) campo.name = `${prefixo}_${sufixo}`;
                });
            });
            if (removeButton) {
                removeButton.setAttribute("aria-label", `Remover seção ${numero}`);
            }
            if (duplicateButton) {
                duplicateButton.setAttribute("aria-label", `Duplicar seção ${numero}`);
            }
        });
    }

    // Limitar ano a 4 dígitos
    function limitarAnoAQuatroDigitos(event) {
        event.target.value = event.target.value.replace(/\D/g, "").slice(0, 4);
    }

    function obterDadosDoFormulario() {
        const dados = {};
        Array.from(form.elements).forEach(function (campo) {
            if (!campo.name || campo.type === "file" || campo.type === "submit" || campo.type === "reset" || campo.disabled) return;
            if (campo.type === "checkbox" || campo.type === "radio") {
                if (!campo.checked) return;
            }
            if (!dados[campo.name]) dados[campo.name] = [];
            dados[campo.name].push(campo.value);
        });
        return dados;
    }

    function salvarRascunho() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(obterDadosDoFormulario()));
        } catch (erro) {
        }
    }

    function restaurarRascunho() {
        let dados;
        try { dados = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null"); } catch (erro) { return; }
        if (!dados) return;

        const autoresSalvos = Object.keys(dados).filter(function (nome) { return /^autor_\d+$/.test(nome); }).length;
        while (autoresContainer.querySelectorAll("input[name^='autor_']").length < autoresSalvos) adicionarAutor({ preventDefault: function () {} });
        const secoesSalvas = (dados.secao_titulo || []).length;
        while (secoesContainer.querySelectorAll(".work-section").length < secoesSalvas) adicionarSecao({ preventDefault: function () {} });

        Object.keys(dados).forEach(function (nome) {
            const campos = form.querySelectorAll(`[name="${CSS.escape(nome)}"]`);
            (dados[nome] || []).forEach(function (valor, indice) {
                if (campos[indice]) campos[indice].value = valor;
            });
        });
        renumerarAutores();
        renumerarSecoes();
    }

    // Validar formulário
    function validarFormulario(event) {
        limparErros();

        const erros = [];
        validarCampoObrigatorio("instituicao", "Informe a instituição.", erros);
        validarCampoObrigatorio("professor", "Informe o professor ou professora.", erros);
        validarCampoObrigatorio("cidade", "Informe a cidade.", erros);
        validarCampoObrigatorio("titulo", "Informe o título.", erros);
        validarAutores(erros);
        validarAno(erros);
        validarSecoes(erros);

        if (erros.length > 0) {
            event.preventDefault();
            mostrarErros(erros);
            focarPrimeiroCampoInvalido();
            return;
        }

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = "Gerando DOCX...";
            window.setTimeout(function () {
                submitButton.disabled = false;
                submitButton.textContent = "Gerar DOCX";
            }, 2500);
        }
    }

    // Validar campo obrigatório
    function validarCampoObrigatorio(id, mensagem, erros) {
        const campo = document.getElementById(id);
        if (!campo || campo.value.trim()) {
            return;
        }
        marcarCampoInvalido(campo);
        erros.push(mensagem);
    }

    // Validar autores
    function validarAutores(erros) {
        const autores = Array.from(autoresContainer.querySelectorAll("input[name^='autor_']"));
        const possuiAutor = autores.some(function (autor) {
            return autor.value.trim().length > 0;
        });

        if (!possuiAutor) {
            autores.forEach(marcarCampoInvalido);
            erros.push("Informe pelo menos um autor.");
        }
    }

    // Validar ano
    function validarAno(erros) {
        if (!anoInput) {
            return;
        }

        const ano = anoInput.value.trim();
        if (!/^\d{4}$/.test(ano)) {
            marcarCampoInvalido(anoInput);
            erros.push("Informe o ano com quatro dígitos.");
        }
    }

    // Validar seções
    function validarSecoes(erros) {
        const secoes = secoesContainer.querySelectorAll(".work-section");
        let temSecaoValida = false;

        secoes.forEach(function (secao) {
            const titulo = secao.querySelector("input[name='secao_titulo']");

            if (titulo && titulo.value.trim()) {
                temSecaoValida = true;
            }
        });

        if (!temSecaoValida) {
            secoes.forEach(function (secao) {
                const titulo = secao.querySelector("input[name='secao_titulo']");
                if (titulo) marcarCampoInvalido(titulo);
            });
            erros.push("Informe pelo menos uma seção com título.");
        }
    }

    // Marcar campo inválido
    function marcarCampoInvalido(campo) {
        campo.setAttribute("aria-invalid", "true");
        campo.style.borderColor = "#b42318";
    }

    // Limpar erros
    function limparErros() {
        form.querySelectorAll("[aria-invalid='true']").forEach(function (campo) {
            campo.removeAttribute("aria-invalid");
            campo.style.borderColor = "";
        });

        const alertaAtual = document.querySelector(".client-alert");
        if (alertaAtual) {
            alertaAtual.remove();
        }
    }

    // Mostrar erros
    function mostrarErros(erros) {
        const alerta = document.createElement("section");
        alerta.className = "alerts client-alert";
        alerta.setAttribute("aria-live", "polite");
        alerta.innerHTML = erros.map(function (erro) {
            return `<p class="alert alert-erro">${erro}</p>`;
        }).join("");

        form.parentNode.insertBefore(alerta, form);
    }

    // Mostrar notificação toast
    function mostrarNotificacao(mensagem, tipo) {
        const toast = document.createElement("div");
        toast.className = `notification-toast ${tipo}`;
        toast.textContent = mensagem;
        toast.setAttribute("role", "status");
        toast.setAttribute("aria-live", "polite");

        document.body.appendChild(toast);

        setTimeout(function () {
            toast.style.animation = "slideInRight 0.3s ease-out reverse";
            setTimeout(function () {
                toast.remove();
            }, 300);
        }, 3000);
    }

    // Focar no primeiro campo inválido
    function focarPrimeiroCampoInvalido() {
        const campo = form.querySelector("[aria-invalid='true']");
        if (campo) {
            campo.focus();
            campo.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    }

    // Restaurar formulário
    function restaurarFormulario() {
        window.setTimeout(function () {
            limparErros();
            const camposAutor = autoresContainer.querySelectorAll(".field");
            camposAutor.forEach(function (field, index) {
                if (index > 0) {
                    field.remove();
                }
            });
            renumerarAutores();

            const secoes = secoesContainer.querySelectorAll(".work-section");
            secoes.forEach(function (secao, index) {
                if (index > 0) {
                    secao.remove();
                }
            });
            renumerarSecoes();

            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = "Gerar DOCX";
            }

            mostrarNotificacao("Formulário limpo com sucesso", "success");
        }, 0);
    }
}());
