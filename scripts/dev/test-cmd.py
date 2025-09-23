from django.core.management import get_commands, load_command_class
import django
import os
import sys

# first, setup django
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cousinsmatter.settings')
django.setup()

# then, get the command
cmd = sys.argv[1]
app_name = get_commands().get(cmd)  # ex: 'auth'
cmd = load_command_class(app_name, cmd)

# inspect the arguments added
if hasattr(cmd, 'add_arguments'):
    # argparse actions registered on cmd.parser after create_parser called
    parser = cmd.create_parser('manage.py', cmd)
    for action in parser._actions:
        print(action.option_strings, action.dest, action.help)
else:
    print("No add_arguments method found on the command.")
