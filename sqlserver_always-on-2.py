#!/usr/bin/python3.4
#!/usr/bin/python3.4
# -*- coding: utf-8 -*-

'''
    Nom : monitoring-alwaysOn-Health.py
    Auteur : benchchaoui omar adil
    Description : Script de découvertes des instances et jobs Mssql
'''
import subprocess
import pyodbc
import sys
import os
import json
import socket
from collections import OrderedDict

# Recuperation des parametres
instances = sys.argv[1]
hostname = sys.argv[2]
db_username = sys.argv[3]
db_password = sys.argv[4]
ad_realm = sys.argv[5]
sonde = sys.argv[6]

# Définition des variables statiques
output_directory = '/usr/lib/zabbix/externalscripts/temp_mssql'
db_driver = 'mssql_17'
zabbix_sender = '/usr/bin/zabbix_sender'
zbx_proxy_ip = '127.0.0.1'
zbx_proxy_port = '10052'
SQL_BROWSER_DEFAULT_PORT = 1434
BUFFER_SIZE = 4096
TIMEOUT = 2
data = []
#result = []

def send_to_zabbix(zbx_key_name, value):
    key = '{}[{}]'.format(zbx_key_name, value)
    os.system('{} -s {} --key "{}" --value "{}" -z "{}" -p "{}" > /dev/null'.format(
        zabbix_sender, hostname, key, value, zbx_proxy_ip, zbx_proxy_port))


def get_instance_port(db_hostname, db_instance, sql_browser_port=SQL_BROWSER_DEFAULT_PORT,
                      buffer_size=BUFFER_SIZE, timeout=TIMEOUT):
    # Creation du socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Définir le timeout
    sock.settimeout(timeout)
    server_address = (db_hostname, sql_browser_port)
    # Envoi du packet CLNT_UCAST_INST pour récuperer les infos de l'instance.
    # https://msdn.microsoft.com/en-us/library/cc219746.aspx
    message = '\x04%s\x00' % db_instance
    # Encodage du message en tableau d'octes
    message = message.encode()
    # Envoi des données
    sock.sendto(message, server_address)
    # Reception de la réponse
    data, server = sock.recvfrom(buffer_size)

    results = []

    # Boucler sur le résultat de la connexion.
    for server in data[3:].decode().split(';;'):
        server_info = OrderedDict()
        chunk = server.split(';')
        if len(chunk) > 1:
            for i in range(1, len(chunk), 2):
                server_info[chunk[i - 1]] = chunk[i]

            results.append(server_info)
            instance_port = server_info['tcp']

    # Fermeture de la connexion
    sock.close()
#    print(instance_port)
    return instance_port

def synchronisation_health():
    cursor.execute('''
    select synchronization_health from sys.dm_hadr_database_replica_states where is_primary_replica = 1;
    ''')

    return [i[0] for i in cursor.fetchall()]

def primary_synchronisation_state():
    cursor.execute('''
    select synchronization_state from sys.dm_hadr_database_replica_states where is_primary_replica = 1;
    ''')

    return [i[0] for i in cursor.fetchall()]

def secondary_synchronisation_state():
    cursor.execute('''
    select synchronization_state from sys.dm_hadr_database_replica_states where is_primary_replica = 0;
    ''')

    return [i[0] for i in cursor.fetchall()]

def fetch_data_1(funct, zbx_key_name):
    global data
    for i in funct:
        if i != 2:
            data= [({
                   '{#result}': 0
                   })]
            send_to_zabbix(zbx_key_name, 0)
        else:
            data = [({
                    '{#result}': 2
                    })]
            send_to_zabbix(zbx_key_name, 2)
    return data

def fetch_data_2(funct, zbx_key_name):
    global data
    if 0 in funct:
        data = [({
                '{#result}': 0
                })]
        send_to_zabbix(zbx_key_name, 0)
    else:
        data = [({
                '{#result}': 2
                })]
        send_to_zabbix(zbx_key_name, 2)
    return data


if __name__ == "__main__":

    db_instance = instances

    if ad_realm == 'LOCAL':
        db_port = get_instance_port(hostname, db_instance)
        chaine = 'Driver={};Server={},{};UID={};PWD={}'.format(
            db_driver, hostname, db_port, db_username, db_password)
    elif ad_realm == '1433':
        db_port = 1433
        chaine = 'Driver={};Server={},{};UID={};PWD={}'.format(
            db_driver, hostname, db_port, db_username, db_password)
    else:
        isql_host = '{}.{},{}'.format(hostname, ad_realm, db_port)
        chaine = 'DRIVER={};SERVER={};Trusted_Connection=yes'.format(
            db_driver, isql_host)

    try:
        cnxn = pyodbc.connect(chaine)
    except pyodbc.OperationalError:
        db_port = get_instance_port(hostname, db_instance)
        chaine = 'Driver={};Server={},{};UID={};PWD={}'.format(
            db_driver, hostname, db_port, db_username, db_password)
    # Initialisation du curseur.
    cursor = cnxn.cursor()
    if sonde == 'synchronisation health':
        data = fetch_data_1(synchronisation_health(), 'zs.synchronisation.health')
    elif sonde == 'primary synchronisation state':
        data = fetch_data_2(primary_synchronisation_state(), 'zs.primary.synchronisation.state')
    elif sonde == 'secondary synchronisation state':
        data = fetch_data_2(secondary_synchronisation_state(), 'zs.secondary.synchronisation.state')

    # Une fois le nom des jobs récupérés, on créer ou écrase le fichier JSON.

    #with open("{}{}{}{}{}{}".format(output_directory, '/', hostname, '_', 'jobs', '.json'), 'w+') as outfile:
    #    json.dump({"data": data}, outfile)
    #    outfile.write("\n")
    print(json.dumps({"data": data}, indent=4))
