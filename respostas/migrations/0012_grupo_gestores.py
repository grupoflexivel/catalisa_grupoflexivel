from django.db import migrations

NOME_DO_GRUPO = "Gestores"
CODENAME = "ver_todas_ideias"


def cria_grupo_gestores(apps, schema_editor):
    """
    Cria o grupo "Gestores" já com a permissão de ver todas as ideias.

    A permissão é criada aqui com `get_or_create` porque o Django só materializa
    as permissões de um modelo no sinal `post_migrate` — ou seja, depois desta
    migração. Sem o `get_or_create` a busca falharia numa base nova e passaria
    numa base existente, o que é o pior tipo de bug de deploy.
    """
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    tipo, _ = ContentType.objects.get_or_create(app_label="respostas", model="ideia")

    permissao, _ = Permission.objects.get_or_create(
        codename=CODENAME,
        content_type=tipo,
        defaults={"name": "Pode ver todas as ideias enviadas"},
    )

    grupo, _ = Group.objects.get_or_create(name=NOME_DO_GRUPO)
    grupo.permissions.add(permissao)


def remove_grupo_gestores(apps, schema_editor):
    """
    Desfaz a criação do grupo.

    A permissão em si não é apagada: ela pertence ao modelo e volta a ser criada
    pelo `post_migrate` de qualquer forma.
    """
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name=NOME_DO_GRUPO).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("respostas", "0011_alter_ideia_options"),
        ("auth", "__first__"),
        ("contenttypes", "__first__"),
    ]

    operations = [
        migrations.RunPython(cria_grupo_gestores, remove_grupo_gestores),
    ]
