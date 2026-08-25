import io
import shutil
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from respostas.models import (
    Beneficio,
    Departamento,
    DocumentoIdeia,
    FotoIdeia,
    Ideia,
    UnidadeFabril,
)
from respostas.validators import MAXIMO_DOCUMENTOS, MAXIMO_FOTOS

MEDIA_TEMP = tempfile.mkdtemp()


def imagem(nome="foto.jpg", tamanho=(40, 30)):
    buffer = io.BytesIO()
    Image.new("RGB", tamanho, "green").save(buffer, format="JPEG")
    return SimpleUploadedFile(nome, buffer.getvalue(), content_type="image/jpeg")


def pdf(nome="relatorio.pdf", peso=32):
    return SimpleUploadedFile(nome, b"%PDF-1.4 " + b"x" * peso, content_type="application/pdf")


@override_settings(MEDIA_ROOT=MEDIA_TEMP)
class UploadAnexosTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_TEMP, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        Usuario = get_user_model()
        self.autor = Usuario.objects.create_user(
            username="ana", password="x", nome_completo="Ana Silva", is_active=True,
            must_change_password=False
        )
        self.unidade = UnidadeFabril.objects.create(nome="Planta 1")
        self.depto = Departamento.objects.create(nome="Manutenção")
        self.beneficio = Beneficio.objects.create(nome="Redução de custo")
        self.client.force_login(self.autor)

    def dados(self):
        return {
            "nome_autor": self.autor.pk,
            "unidade_fabril": self.unidade.pk,
            "departamento": self.depto.pk,
            "forma_de_participacao": "IND",
            "titulo": "Trocar o filtro",
            "descricao_problema": "a", "impacto_problema": "b", "causa_problema": "c",
            "descricao_ideia": "d", "como_a_ideia_resolve_problema": "e",
            "participacao_implementacao": "Sim",
            "beneficios": [self.beneficio.pk],
            "ganhos_esperados": "f", "necessidades_ideia": "g",
            "valor_estimado_ideia": "R$ 100", "prazo_estimado_ideia": "1 mês",
        }

    def test_envia_varias_fotos_e_documentos(self):
        resposta = self.client.post(
            reverse("cadastrar_ideia"),
            {
                **self.dados(),
                "fotos": [imagem("a.jpg"), imagem("b.jpg"), imagem("c.jpg")],
                "documentos": [pdf("Relatório final.pdf"), pdf("planilha.pdf")],
            },
        )
        self.assertEqual(resposta.status_code, 302)

        ideia = Ideia.objects.get()
        self.assertEqual(ideia.fotos.count(), 3)
        self.assertEqual(ideia.documentos.count(), 2)
        self.assertTrue(ideia.tem_anexos)

        foto = ideia.fotos.first()
        self.assertIn("/fotos/", foto.arquivo.name)
        self.assertNotIn("a.jpg", foto.arquivo.name)          # nome virou UUID
        self.assertEqual(
            ideia.documentos.first().nome_exibido, "Relatório final.pdf"
        )

    def test_ideia_sem_anexo_continua_valida(self):
        resposta = self.client.post(reverse("cadastrar_ideia"), self.dados())
        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(Ideia.objects.get().tem_anexos)

    def test_limite_de_fotos(self):
        fotos = [imagem(f"{indice}.jpg") for indice in range(MAXIMO_FOTOS + 1)]
        resposta = self.client.post(reverse("cadastrar_ideia"), {**self.dados(), "fotos": fotos})

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(
            f"no máximo {MAXIMO_FOTOS} fotos",
            str(resposta.context["form"].errors["fotos"]),
        )
        self.assertEqual(Ideia.objects.count(), 0)

    def test_limite_de_documentos(self):
        documentos = [pdf(f"{indice}.pdf") for indice in range(MAXIMO_DOCUMENTOS + 1)]
        resposta = self.client.post(
            reverse("cadastrar_ideia"), {**self.dados(), "documentos": documentos}
        )

        self.assertIn(
            f"no máximo {MAXIMO_DOCUMENTOS} documentos",
            str(resposta.context["form"].errors["documentos"]),
        )

    def test_extensao_recusada_identifica_o_arquivo(self):
        malicioso = SimpleUploadedFile(
            "payload.svg", b"<svg onload=alert(1)>", content_type="image/svg+xml"
        )
        resposta = self.client.post(
            reverse("cadastrar_ideia"),
            {**self.dados(), "documentos": [pdf("ok.pdf"), malicioso]},
        )

        erros = str(resposta.context["form"].errors["documentos"])
        self.assertIn("payload.svg", erros)
        self.assertEqual(Ideia.objects.count(), 0)

    def test_tamanho_recusado(self):
        grande = SimpleUploadedFile(
            "grande.pdf", b"x" * (11 * 1024 * 1024), content_type="application/pdf"
        )
        resposta = self.client.post(
            reverse("cadastrar_ideia"), {**self.dados(), "documentos": [grande]}
        )
        self.assertIn("e o limite é", str(resposta.context["form"].errors["documentos"]))

    def test_download_exige_permissao(self):
        self.client.post(reverse("cadastrar_ideia"), {**self.dados(), "fotos": [imagem()]})
        foto = FotoIdeia.objects.get()
        url = reverse("baixar_anexo_ideia", args=["foto", foto.pk])

        # A autora (remetente) baixa o próprio anexo.
        self.assertEqual(self.client.get(url).status_code, 200)

        # Outro colaborador, não.
        Usuario = get_user_model()
        intruso = Usuario.objects.create_user(
            username="bob", password="x", nome_completo="Bob", must_change_password=False
        )
        self.client.force_login(intruso)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_tipo_invalido_na_url(self):
        self.client.post(reverse("cadastrar_ideia"), {**self.dados(), "fotos": [imagem()]})
        url = reverse("baixar_anexo_ideia", args=["ideia", 1])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_apagar_ideia_remove_arquivos_do_disco(self):
        self.client.post(
            reverse("cadastrar_ideia"),
            {**self.dados(), "fotos": [imagem()], "documentos": [pdf()]},
        )
        ideia = Ideia.objects.get()
        caminhos = [Path(foto.arquivo.path) for foto in ideia.fotos.all()]
        caminhos += [Path(doc.arquivo.path) for doc in ideia.documentos.all()]
        self.assertTrue(all(caminho.exists() for caminho in caminhos))

        # O gancho de limpeza roda em transaction.on_commit, que dentro de
        # TestCase só dispara sob captureOnCommitCallbacks.
        with self.captureOnCommitCallbacks(execute=True):
            ideia.delete()

        self.assertEqual(FotoIdeia.objects.count(), 0)
        self.assertEqual(DocumentoIdeia.objects.count(), 0)
        self.assertFalse(any(caminho.exists() for caminho in caminhos))


class AcessoGestorTest(TestCase):
    """
    Permissão granular da aba de ideias.
    """

    def setUp(self):
        Usuario = get_user_model()
        self.comum = Usuario.objects.create_user(
            username="ana", password="x", nome_completo="Ana Silva", must_change_password=False
        )
        self.gestor = Usuario.objects.create_user(
            username="gil", password="x", nome_completo="Gil Souza", must_change_password=False
        )
        self.gestor.groups.add(Group.objects.get(name="Gestores"))

        self.admin = Usuario.objects.create_superuser(
            username="root", password="x", nome_completo="Raiz", must_change_password=False
        )

    def test_grupo_criado_pela_migracao_ja_tem_a_permissao(self):
        grupo = Group.objects.get(name="Gestores")
        self.assertTrue(
            grupo.permissions.filter(codename="ver_todas_ideias").exists()
        )

    def test_colaborador_comum_nao_entra(self):
        self.client.force_login(self.comum)
        resposta = self.client.get(reverse("listar_ideias"))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("login"), resposta["Location"])

    def test_gestor_entra(self):
        self.client.force_login(self.gestor)
        self.assertEqual(self.client.get(reverse("listar_ideias")).status_code, 200)

    def test_administrador_continua_entrando_sem_estar_no_grupo(self):
        self.assertFalse(self.admin.groups.exists())
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("listar_ideias")).status_code, 200)

    def test_gestor_abre_o_modal_de_detalhe(self):
        ideia = _ideia_minima(self.comum)
        self.client.force_login(self.gestor)
        resposta = self.client.get(reverse("detalhe_ideia", args=[ideia.pk]))
        self.assertEqual(resposta.status_code, 200)

    def test_gestor_baixa_anexo_de_ideia_alheia(self):
        # A ideia é de um terceiro: se fosse da `comum`, ela passaria pela regra
        # "o autor vê os próprios anexos" e o teste não provaria nada.
        ideia = _ideia_minima(self.admin)
        foto = FotoIdeia.objects.create(ideia=ideia, arquivo=imagem())

        self.client.force_login(self.gestor)
        url = reverse("baixar_anexo_ideia", args=["foto", foto.pk])
        self.assertEqual(self.client.get(url).status_code, 200)

        # Já um colaborador sem a permissão continua barrado.
        self.client.force_login(self.comum)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_aba_aparece_no_menu_so_para_quem_tem_a_permissao(self):
        # O href completo, e não só a URL: `/ideias/` também é prefixo de
        # `/ideias/cadastro/`, o link "Nova ideia" que todo mundo enxerga.
        link = f'href="{reverse("listar_ideias")}"'

        self.client.force_login(self.comum)
        self.assertNotContains(self.client.get(reverse("cadastrar_ideia")), link)

        self.client.force_login(self.gestor)
        self.assertContains(self.client.get(reverse("cadastrar_ideia")), link)


def _ideia_minima(autor):
    """Ideia enviada por `autor`, com o mínimo de campos obrigatórios."""
    return Ideia.objects.create(
        nome_autor=autor.nome_completo,
        unidade_fabril=UnidadeFabril.objects.create(nome="Planta 2"),
        departamento=Departamento.objects.create(nome="Qualidade"),
        forma_de_participacao="IND",
        titulo="Ideia de teste",
        descricao_problema="a", impacto_problema="b", causa_problema="c",
        descricao_ideia="d", como_a_ideia_resolve_problema="e",
        participacao_implementacao="Sim",
        ganhos_esperados="f", necessidades_ideia="g",
        valor_estimado_ideia="R$ 1", prazo_estimado_ideia="1 dia",
        usuario_remetente_ideia=str(autor),
    )
