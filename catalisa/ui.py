"""
Tokens de interface compartilhados entre os formulários da aplicação.

As classes abaixo são utilitários do Tailwind + componentes do daisyUI aplicados
aos widgets renderizados pelo Django. Ficam centralizadas aqui para que a
aparência dos campos seja idêntica em todos os formulários e para que uma
mudança de design não precise ser replicada em cada `forms.py`.
"""

INPUT_CLASS = "input w-full h-12 rounded-xl bg-base-100 text-base"
SELECT_CLASS = "select w-full h-12 rounded-xl bg-base-100 text-base"
TEXTAREA_CLASS = "textarea w-full rounded-xl bg-base-100 text-base leading-relaxed"

# RadioSelect e CheckboxSelectMultiple repetem o atributo `class` no container
# e em cada <input>, o que quebraria os componentes do daisyUI. Esses grupos são
# estilizados por estrutura, a partir do wrapper `.exp-choices` no template.


def aplica_estilo_campos(form, placeholders=None, classe=INPUT_CLASS):
    """
    Aplica as classes visuais aos widgets de um formulário já existente.

    Complementa (em vez de substituir) as classes declaradas no widget, o que
    permite estilizar formulários herdados do Django sem reescrever seus campos.

    Args:
        form: Formulário cujos widgets serão estilizados.
        placeholders (dict | None): Mapa opcional de `nome_do_campo -> placeholder`.
        classe (str): Classes aplicadas a cada widget.
    """
    placeholders = placeholders or {}

    for nome, campo in form.fields.items():
        classes_atuais = campo.widget.attrs.get("class", "")
        campo.widget.attrs["class"] = f"{classes_atuais} {classe}".strip()

        if nome in placeholders:
            campo.widget.attrs["placeholder"] = placeholders[nome]
