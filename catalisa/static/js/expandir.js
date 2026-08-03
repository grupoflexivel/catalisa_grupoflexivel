/* ==========================================================================
   Programa Expandir — comportamentos de interface
   Vanilla JS, sem dependências. Tudo por delegação de eventos para continuar
   funcionando em conteúdo trocado pelo HTMX.
   ========================================================================== */
(function () {
  "use strict";

  /* ---------------------------------------------------------------- utils */
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  /* -------------------------------------------------- barra de progresso */
  const progress = () => document.getElementById("exp-progress");

  document.addEventListener("htmx:beforeRequest", function () {
    const bar = progress();
    if (!bar) return;
    bar.classList.remove("is-done");
    bar.classList.add("is-loading");
  });

  function finishProgress() {
    const bar = progress();
    if (!bar) return;
    bar.classList.remove("is-loading");
    bar.classList.add("is-done");
    window.setTimeout(() => bar.classList.remove("is-done"), 500);
  }

  document.addEventListener("htmx:afterRequest", finishProgress);
  document.addEventListener("htmx:responseError", finishProgress);
  document.addEventListener("htmx:sendError", function () {
    finishProgress();
    showToast("Falha de conexão com o servidor. Verifique sua rede e tente novamente.", "error");
  });

  /* ------------------------------------------------------------- toasts  */
  function dismissToast(el) {
    if (!el) return;
    el.style.transition = "opacity .25s ease, transform .25s ease";
    el.style.opacity = "0";
    el.style.transform = "translateX(12px)";
    window.setTimeout(() => el.remove(), 260);
  }

  function scheduleToasts(root) {
    $$(".exp-toast", root).forEach(function (toast) {
      if (toast.dataset.scheduled) return;
      toast.dataset.scheduled = "1";
      window.setTimeout(() => dismissToast(toast), 6000);
    });
  }

  function showToast(text, kind) {
    const host = document.getElementById("exp-toasts");
    if (!host) return;
    const map = { success: "alert-success", error: "alert-error", warning: "alert-warning" };
    const toast = document.createElement("div");
    toast.className =
      "exp-toast alert exp-fade-up w-[min(24rem,calc(100vw-2rem))] items-start gap-3 rounded-2xl border shadow-lg " +
      (map[kind] || "alert-info");
    toast.setAttribute("role", "status");
    toast.innerHTML =
      '<span class="flex-1 text-sm font-medium leading-snug"></span>' +
      '<button type="button" class="btn btn-ghost btn-xs btn-circle" data-dismiss-toast aria-label="Fechar">✕</button>';
    toast.firstElementChild.textContent = text;
    host.appendChild(toast);
    scheduleToasts(host);
  }

  document.addEventListener("click", function (event) {
    const btn = event.target.closest("[data-dismiss-toast]");
    if (btn) dismissToast(btn.closest(".exp-toast"));
  });

  /* Mensagens enviadas pelo servidor em respostas HTMX (header HX-Trigger) */
  document.body.addEventListener("expandir:toast", function (event) {
    const data = event.detail || {};
    if (data.message) showToast(data.message, data.level);
  });

  /* --------------------------------------------------- senha: mostrar/ocultar */
  document.addEventListener("click", function (event) {
    const btn = event.target.closest("[data-toggle-password]");
    if (!btn) return;

    const field = document.getElementById(btn.getAttribute("data-toggle-password"));
    if (!field) return;

    const hidden = field.getAttribute("type") === "password";
    field.setAttribute("type", hidden ? "text" : "password");
    btn.setAttribute("aria-label", hidden ? "Ocultar senha" : "Mostrar senha");

    const use = btn.querySelector("use");
    if (use) use.setAttribute("href", hidden ? "#i-eye-off" : "#i-eye");
  });

  /* -------------------------------------------------------------- modais */
  function openDialogIn(container) {
    const dialog = container.querySelector("dialog");
    if (!dialog || dialog.open) return;
    dialog.showModal();
    dialog.addEventListener("close", () => {
      window.setTimeout(() => {
        if (dialog.parentElement) dialog.parentElement.innerHTML = "";
      }, 150);
    });
  }

  document.addEventListener("htmx:afterSwap", function (event) {
    const target = event.detail && event.detail.target;
    if (!target) return;

    if (target.id === "exp-modal") openDialogIn(target);

    // Em trocas com outerHTML o alvo original já foi substituído, então a
    // reinicialização roda sobre o documento. Todas as rotinas são idempotentes.
    scheduleToasts(document);
    syncConditionalFields(document);
    initPickers(document);
    initCounters(document);
    syncTodosOsFiltros(document);
    focarPrimeiroErro(document);
  });

  /* Leva o usuário até o primeiro campo com erro após um envio recusado */
  function focarPrimeiroErro(root) {
    const invalido = root.querySelector(".exp-field--invalid");
    if (!invalido) return;

    invalido.scrollIntoView({ behavior: "smooth", block: "center" });
    const controle = invalido.querySelector("input, select, textarea");
    if (controle && controle.type !== "hidden") {
      window.setTimeout(() => controle.focus({ preventScroll: true }), 350);
    }
  }

  /* ------------------------------------------- campos condicionais do form
     Um bloco com [data-show-when="<name>"] [data-show-values="A|B"] aparece
     somente quando algum input com aquele name e valor está marcado.
     Com [data-show-when-label] a comparação usa o texto do rótulo.
  ------------------------------------------------------------------------ */
  function isTriggered(block) {
    const name = block.getAttribute("data-show-when");
    const values = (block.getAttribute("data-show-values") || "")
      .split("|")
      .map((v) => v.trim().toLowerCase())
      .filter(Boolean);
    const byLabel = block.hasAttribute("data-show-when-label");

    return $$('input[name="' + name + '"]').some(function (input) {
      if (!input.checked) return false;
      const value = (input.value || "").trim().toLowerCase();
      if (values.includes(value)) return true;
      if (!byLabel) return false;
      const label = input.closest("label") || input.parentElement;
      const text = label ? label.textContent.trim().toLowerCase() : "";
      return values.some((v) => text.includes(v));
    });
  }

  function syncConditionalFields(root) {
    $$("[data-show-when]", root).forEach(function (block) {
      const active = isTriggered(block);
      block.classList.toggle("hidden", !active);
      block.setAttribute("aria-hidden", active ? "false" : "true");
    });
  }

  document.addEventListener("change", function (event) {
    if (event.target.matches('input[type="radio"], input[type="checkbox"]')) {
      syncConditionalFields(document);
    }
  });

  /* --------------------------------------------- seletor de pessoas (chips)
     <div data-exp-picker data-max="3"> com um input[data-picker-search] e
     rótulos .exp-choice contendo checkboxes.
  ------------------------------------------------------------------------ */
  function refreshPicker(picker) {
    const max = parseInt(picker.getAttribute("data-max") || "0", 10);
    const boxes = $$('input[type="checkbox"]', picker);
    const selected = boxes.filter((b) => b.checked);
    const counter = $("[data-picker-count]", picker);
    const chips = $("[data-picker-chips]", picker);

    if (counter) {
      counter.textContent = max
        ? selected.length + " de " + max + " selecionado" + (selected.length === 1 ? "" : "s")
        : selected.length + " selecionado" + (selected.length === 1 ? "" : "s");
      counter.classList.toggle("text-warning", max > 0 && selected.length >= max);
    }

    if (max > 0) {
      boxes.forEach(function (box) {
        const disabled = !box.checked && selected.length >= max;
        box.disabled = disabled;
        const row = box.closest("label");
        if (row) row.classList.toggle("opacity-40", disabled);
      });
    }

    if (chips) {
      chips.innerHTML = "";
      selected.forEach(function (box) {
        const label = box.closest("label");
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className =
          "badge badge-lg gap-1 rounded-full border-primary/20 bg-primary/10 px-3 py-3 text-xs font-semibold text-primary transition hover:bg-primary/20";
        chip.textContent = label ? label.textContent.trim() : box.value;
        chip.insertAdjacentHTML("beforeend", '<span class="ml-1 text-sm leading-none">&times;</span>');
        chip.addEventListener("click", function () {
          box.checked = false;
          refreshPicker(picker);
        });
        chips.appendChild(chip);
      });
      chips.classList.toggle("hidden", selected.length === 0);
    }
  }

  /* Valor escolhido no campo nomeado por [data-picker-exclude-field] — o autor da
     ideia, que não pode figurar também como integrante da própria equipe.
     Atende tanto um grupo de radios quanto uma lista suspensa. */
  function valorExcluido(picker) {
    const nome = picker.getAttribute("data-picker-exclude-field");
    if (!nome) return "";

    const campo = document.querySelector(
      '[name="' + nome + '"]:checked, select[name="' + nome + '"]'
    );

    return campo ? campo.value : "";
  }

  /* Decide quais opções ficam visíveis: combina o termo da busca com a exclusão
     do autor. A opção excluída também é desmarcada, para que alguém escolhido
     antes da troca de autor não permaneça selecionado. */
  function filtraOpcoes(picker) {
    const search = $("[data-picker-search]", picker);
    const termo = (search ? search.value : "").trim().toLowerCase();
    const excluido = valorExcluido(picker);

    let visiveis = 0;
    let desmarcou = false;

    $$("[data-picker-option]", picker).forEach(function (option) {
      const box = $("input", option);
      const ehOAutor = !!excluido && !!box && box.value === excluido;

      if (ehOAutor && box.checked) {
        box.checked = false;
        desmarcou = true;
      }

      const combina = !termo || option.textContent.toLowerCase().includes(termo);
      const oculto = ehOAutor || !combina;

      option.classList.toggle("hidden", oculto);
      if (!oculto) visiveis += 1;
    });

    const vazio = $("[data-picker-empty]", picker);
    if (vazio) vazio.classList.toggle("hidden", visiveis > 0);

    if (desmarcou) refreshPicker(picker);
  }

  function initPickers(root) {
    $$("[data-exp-picker]", root).forEach(function (picker) {
      if (picker.dataset.ready) return;
      picker.dataset.ready = "1";

      const search = $("[data-picker-search]", picker);
      if (search) {
        search.addEventListener("input", function () {
          filtraOpcoes(picker);
        });
      }

      picker.addEventListener("change", function (event) {
        if (event.target.matches('input[type="checkbox"]')) refreshPicker(picker);
      });

      refreshPicker(picker);
      filtraOpcoes(picker);
    });
  }

  /* Trocar o autor reavalia a lista de integrantes na hora */
  function reavaliaExclusoes(event) {
    const nome = event.target.name;
    if (!nome) return;
    $$('[data-picker-exclude-field="' + nome + '"]').forEach(function (picker) {
      filtraOpcoes(picker);
    });
  }

  document.addEventListener("change", reavaliaExclusoes);
  document.addEventListener("input", reavaliaExclusoes);

  /* ------------------------------------------------ contador de caracteres */
  function initCounters(root) {
    $$("textarea[maxlength], input[data-counter][maxlength]", root).forEach(function (field) {
      if (field.dataset.counterReady) return;
      const target = document.querySelector('[data-counter-for="' + field.id + '"]');
      if (!target) return;
      field.dataset.counterReady = "1";

      const max = field.getAttribute("maxlength");
      const update = function () {
        target.textContent = field.value.length + "/" + max;
        target.classList.toggle("text-warning", field.value.length > max * 0.9);
      };
      field.addEventListener("input", update);
      update();
    });
  }

  /* ------------------------------------------ filtros da listagem de ideias
     O botão "Limpar filtros" fica fora do container trocado pelo HTMX, então o
     estado que veio do servidor congela no primeiro carregamento. Aqui ele é
     reavaliado a cada alteração do formulário.
  ------------------------------------------------------------------------ */
  function camposDoFiltro(form) {
    return $$("input[name], select[name]", form);
  }

  function syncLimparFiltros(form) {
    const botao = $("[data-limpar-filtros]", form);
    if (!botao) return;

    const ativo = camposDoFiltro(form).some((campo) => (campo.value || "").trim() !== "");
    botao.classList.toggle("pointer-events-none", !ativo);
    botao.classList.toggle("opacity-40", !ativo);
    botao.setAttribute("aria-disabled", ativo ? "false" : "true");
  }

  function syncTodosOsFiltros(root) {
    $$("[data-limpar-filtros]", root).forEach(function (botao) {
      const form = botao.closest("form");
      if (form) syncLimparFiltros(form);
    });
  }

  function aoAlterarFiltro(event) {
    const form = event.target.closest ? event.target.closest("form") : null;
    if (form && $("[data-limpar-filtros]", form)) syncLimparFiltros(form);
  }

  document.addEventListener("input", aoAlterarFiltro);
  document.addEventListener("change", aoAlterarFiltro);

  /* Esvazia os campos antes do HTMX montar a requisição. form.reset() não serve:
     ele restaura os valores que vieram no HTML, que já contêm os filtros da URL. */
  document.addEventListener("click", function (event) {
    const botao = event.target.closest("[data-limpar-filtros]");
    if (!botao) return;

    const form = botao.closest("form");
    if (!form) return;

    camposDoFiltro(form).forEach(function (campo) {
      campo.value = "";
    });
    syncLimparFiltros(form);
  }, true);

  /* ------------------------------------------- fechar drawer ao navegar */
  document.addEventListener("click", function (event) {
    if (event.target.closest(".drawer-side a")) {
      const toggle = document.getElementById("exp-drawer");
      if (toggle) toggle.checked = false;
    }
  });

  /* ------------------------------------------------------------- arranque */
  function boot() {
    scheduleToasts(document);
    syncConditionalFields(document);
    initPickers(document);
    initCounters(document);
    syncTodosOsFiltros(document);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
