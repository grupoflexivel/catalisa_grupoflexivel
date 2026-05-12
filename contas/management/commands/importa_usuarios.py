import csv
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Realiza a importação dos usuários de um .CSV para subir na aplicação'

    def add_arguments(self,parser):
        parser.add_argument('csv_file', type=str)

    def handle(self,*args,**options):
        path = options['csv_file']
        with open(path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file,delimiter=';')
            print(reader.fieldnames)

            for row in reader:
                if not User.objects.filter(username=row['username']).exists():
                    User.objects.create_user(
                        username=row['username'],
                        nome_completo=row['nome'],
                        password=row['password']
                    )
                    self.stdout.write(self.style.SUCCESS(f"Usuário {row['username']}"))
                
                else:
                    self.stdout.write(self.style.WARNING(f"Usuário {row['username']} já existe"))
    
                    