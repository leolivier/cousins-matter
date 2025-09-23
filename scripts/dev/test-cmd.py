from django.core.management import get_commands, load_command_class
import django
import os
import sys

os_name = None
# initialisation si nécessaire
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cousinsmatter.settings')
django.setup()
cmd = sys.argv[1]
# obtenir le module de la commande
app_name = get_commands().get(cmd)  # ex: 'auth'
cmd = load_command_class(app_name, cmd)

# inspecter les arguments ajoutés
if hasattr(cmd, 'add_arguments'):
    # argparse actions enregistrées sur cmd.parser after create_parser called
    parser = cmd.create_parser('manage.py', cmd)
    for action in parser._actions:
        print(action.option_strings, action.dest, action.help)
else:
    print("Pas d'add_arguments ; vérifier la source de la commande.")
