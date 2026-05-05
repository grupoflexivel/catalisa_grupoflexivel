from django.shortcuts import redirect
from django.urls import reverse

class ForcePasswordChangeMiddleware:
    """
    Intercepta requisições para forçar a troca da senha inicial.

    Verifica se o usuário autenticado possui a flag `must_change_password` 
    ativa. Caso positivo, restringe o acesso apenas às URLs de troca de 
    senha e logout, redirecionando qualquer outra tentativa de acesso.
    """
    def __init__(self, get_response):
        """
        Inicializa o middleware com a função de próxima resposta na pilha.

        Args:
            get_response (callable): A próxima etapa no processamento da requisição.
        """
        self.get_response = get_response
    
    def __call__(self, request):
        """
        Processa a requisição e aplica a lógica de redirecionamento forçado.

        Ignora usuários não autenticados e rotas de sistema (admin, static, media).
        Se o usuário precisar trocar a senha e tentar acessar uma rota não 
        permitida, será enviado para a página de troca de senha.

        Args:
            request (HttpRequest): O objeto da requisição atual.

        Returns:
            HttpResponse: A resposta final ou um redirecionamento para a troca de senha.
        """
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Impede de entrar em loop ao acessar essas URLs
        if request.path.startswith(("/admin/", "/static/", "/media/")):
            return self.get_response(request)
        
        user = request.user

        # Define as rotas que o usuário PODE acessar mesmo precisando trocar a senha
        allowed_paths = {
            reverse("troca_senha"),
            #reverse("URL DA TROCA DE SENHA BEM SUCEDIDA"),
            reverse("logout")
        }
        
        current_path = request.path_info
        # Recupera a flag com fallback para False caso o atributo não exista no modelo
        user_must_change_password = getattr(user, "must_change_password", False)

        # Valida se o usuário está tentando acessar algo fora das allowed_paths
        if user_must_change_password and current_path not in allowed_paths:
            return redirect("troca_senha")
        
        return self.get_response(request)