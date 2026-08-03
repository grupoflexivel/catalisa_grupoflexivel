from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from catalisa.ui import aplica_estilo_campos

Usuario = get_user_model()


class FormularioLogin(AuthenticationForm):
    """
    Formulário de autenticação com a aparência do programa Expandir.

    Herda todo o comportamento do AuthenticationForm padrão do Django e apenas
    ajusta widgets, rótulos e atributos de acessibilidade/autocomplete.

    A mensagem de credencial inválida é reescrita porque a padrão do Django
    interpola o `verbose_name` do campo de login ("user", definido em
    contas/models.py) dentro do texto traduzido, produzindo
    "Por favor, entre com um user e senha corretos...".
    """

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Usuário ou senha incorretos.\n"
        "Verifique se o Caps Lock está ativado.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        aplica_estilo_campos(self, placeholders={
            "username": "seu.usuario",
            "password": "••••••••",
        })

        self.fields["username"].label = "Usuário"
        self.fields["password"].label = "Senha"
        self.fields["username"].widget.attrs.update({
            "autocomplete": "username",
            "autofocus": True,
        })
        self.fields["password"].widget.attrs["autocomplete"] = "current-password"


class FormularioCriacaoUsuarioCustomizado(UserCreationForm):
    """
    Formulário utilizado para a criação de novos usuários no sistema.

    Herda de UserCreationForm para reaproveitar a validação de senha,
    confirmação de senha e criação segura do usuário.
    """
    class Meta:
        model = Usuario
        fields = ('username','nome_completo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        aplica_estilo_campos(self, placeholders={
            "username": "nome.sobrenome",
            "nome_completo": "Nome completo do colaborador",
            "password1": "Senha inicial",
            "password2": "Repita a senha",
        })

        self.fields["username"].label = "Usuário de acesso"
        self.fields["nome_completo"].label = "Nome completo"
        self.fields["password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"


class FormularioTrocaSenhaPrimeiroLogin(SetPasswordForm):
    """
    Formulário utilizado para trocar a senha no primeiro acesso e/ou após a troca de senha por um administrador.

    Herda de SetPasswordForm para reaproveitar os campos de nova senha,
    validações padrão do Django e salvamento seguro com hash.

    Regra adicional: impede que o usuário defina a mesma senha que já estava em uso.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        aplica_estilo_campos(self, placeholders={
            "new_password1": "Nova senha",
            "new_password2": "Repita a nova senha",
        })

        self.fields["new_password1"].label = "Nova senha"
        self.fields["new_password2"].label = "Confirmar nova senha"

    def clean_new_password1(self):
        """Valida se a nova senha é diferente da senha atual.

        Returns:
            str: A nova senha validada.

        Raises:
            ValidationError: Se a nova senha for igual à senha atual.
        """
        password1 = self.cleaned_data.get("new_password1")

        if self.user.check_password(password1):
            raise ValidationError("A nova senha não pode ser igual a atual")

        return password1
    
class FormularioResetarSenha(forms.Form):
    """
    Permite que administradores redefinam a senha de um usuário específico.

    O formulário valida a existência do usuário, a coincidência das senhas,
    os requisitos de complexidade do Django e marca o usuário para 
    troca obrigatória no próximo acesso.
    """
    username = forms.CharField(label="Usuário", max_length=150)
    new_password1 = forms.CharField(label='Nova senha',
                                widget=forms.PasswordInput)
    new_password2 = forms.CharField(label='Confirmar nova senha',
                                widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        aplica_estilo_campos(self, placeholders={
            "username": "Usuário que terá a senha redefinida",
            "new_password1": "Senha temporária",
            "new_password2": "Repita a senha temporária",
        })

        self.fields["username"].widget.attrs["autocomplete"] = "off"

    def clean_username(self):
        """ Valida a existência do username e carrega a instância do usuário.

        Returns:
            str: O username validado.

        Raises:
            ValidationError: Caso o usuário não seja encontrado no banco.
        """
        username = self.cleaned_data.get("username")
        try:
            self.user = Usuario.objects.get(username=username)
        except Usuario.DoesNotExist:
            raise ValidationError("Usuário não encontrado.")

        return username
    
    def clean(self):
        """
        Executa validações cruzadas e de complexidade de senha.

        Verifica se as senhas coincidem, se a nova senha é diferente da 
        atual e se atende às políticas de segurança configuradas.

        Returns:
            dict: O dicionário de dados limpos (cleaned_data).

        Raises:
            ValidationError: Se qualquer regra de negócio for violada.
        """
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")

        if not hasattr(self,'user') or not password1 or not password2:
            return cleaned_data
        
        if password1 != password2:
            raise ValidationError("As senhas não coincidem.")

        if self.user.check_password(password1):
            raise ValidationError("A nova senha não pode ser igual à senha atual.")

        validate_password(password1, self.user)

        return cleaned_data
    
    def save(self):
        """
        Persiste a nova senha com hash e ativa a flag de troca obrigatória.

        A senha é processada via set_password() para garantir o hashing.

        Returns:
            Usuario: A instância do usuário atualizada.
        """
        password = self.cleaned_data["new_password1"]

        user = self.user

        user.set_password(password)
        user.must_change_password = True
        user.save(update_fields=["password", "must_change_password"])

        return user