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

# Définition des variables statiques
output_directory = '/usr/lib/zabbix/externalscripts/temp_mssql'
db_driver = 'mssql_17'
zabbix_sender = '/usr/bin/zabbix_sender'
zbx_proxy_ip = '127.0.0.1'
zbx_proxy_port = '10052'
data = []
groups = []
discovered_inst = []
SQL_BROWSER_DEFAULT_PORT = 1434
BUFFER_SIZE = 4096
TIMEOUT = 2

def send_to_zabbix(zbx_key_name, param, value):
    key = '{}[{}]'.format(zbx_key_name, param)
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
    return instance_port

def get_mssql_jobs_status():
    cursor.execute('''
    DECLARE @HADRSERVERNAME VARCHAR(25)
    SET @HADRSERVERNAME = @@SERVERNAME
    SELECT CLUSTERNODES.GROUP_NAME          AS [AVAILABILITY GROUP NAME],
       CLUSTERNODES.REPLICA_SERVER_NAME AS [AVAILABILITY REPLICA NAME],
       CLUSTERNODES.NODE_NAME           AS [AVAILABILITY NODE],
       RS.ROLE_DESC                     AS [ROLE],
       DB_NAME(DRS.DATABASE_ID)         AS [AVAILABILITY DATABASE],
       DRS.SYNCHRONIZATION_STATE_DESC   AS [SYNCHRONIZATION STATUS],
       DRS.SYNCHRONIZATION_HEALTH_DESC  AS [SYNCHRONIZATION HEALTH]
    FROM   SYS.DM_HADR_AVAILABILITY_REPLICA_CLUSTER_NODES CLUSTERNODES
       JOIN SYS.DM_HADR_AVAILABILITY_REPLICA_CLUSTER_STATES CLUSTERSTATS
         ON CLUSTERNODES.REPLICA_SERVER_NAME = CLUSTERSTATS.REPLICA_SERVER_NAME
       JOIN SYS.DM_HADR_AVAILABILITY_REPLICA_STATES RS
         ON RS.REPLICA_ID = CLUSTERSTATS.REPLICA_ID
       JOIN SYS.DM_HADR_DATABASE_REPLICA_STATES DRS
         ON RS.REPLICA_ID = DRS.REPLICA_ID
    WHERE  CLUSTERNODES.REPLICA_SERVER_NAME <> @HADRSERVERNAME
    ''')

    groups_rows = cursor.fetchall()
    for row in groups_rows:
        groups.append({
            'Availability_group_name': row[0],
            'Availability_replica_name': row[1],
            'Availability_node': row[2],
            'Role': row[3],
            'Availability_database': row[4],
            'Synchronization_status': row[5],
            'Synchronization_health': row[6]
        })

    for group in groups:
        zbx_key_name = 'zs.availabilty'
        #send_to_zabbix(zbx_key_name+'.group.name', )
        send_to_zabbix(zbx_key_name+'.replica.name', group['Availability_database'], group['Availability_replica_name'])
        send_to_zabbix(zbx_key_name+'.node', group['Availability_database'], group['Availability_node'])
        send_to_zabbix(zbx_key_name+'.synchronization.health', group['Availability_database'], group['Synchronization_health'])
        send_to_zabbix(zbx_key_name+'.role', group['Availability_database'], group['Role'])
        send_to_zabbix(zbx_key_name+'.synchronization.status', group['Availability_database'], group['Synchronization_status'])
        send_to_zabbix(zbx_key_name+'.group.name', group['Availability_database'], group['Availability_group_name'])

        data.append({
            '{#AVAILABILITY_GROUP_NAME}': group['Availability_group_name'],
            '{#AVAILABILITY_REPLICA_NAME}': group['Availability_replica_name'],
            '{#AVAILABILITY_NODE}': group['Availability_node'],
            '{#SYNCHRONIZATION_HEALTH}': group['Synchronization_health'],
            '{#ROLE}': group['Role'],
            '{#AVAILABILITY_DATABASE}': group['Availability_database'],
            '{#SYNCHRONIZATION_STATUS}': group['Synchronization_status']
        })
    return data

def disco_inst():
    for chaine in instances.split('|'):
        param_inst = chaine.split(";")

    #Tentative de récuperation du port de du nom de l'instance
    db_port = param_inst[0]
    if len(param_inst) > 1:
        db_instance = param_inst[1]
    else:
        db_instance = 'MSSQL'

    if '0000' in db_port:
        try:
            # Récupération du port via SQLBrowser
            db_port = get_instance_port(hostname, db_instance)
        except socket.error as error:
            # Si la récupération du port échoue, on ne l'injecte pas dans la liste.
            pass
    discovered_inst.append('{};{}'.format(db_port,db_instance))
    return discovered_inst

if __name__ == "__main__":
    
    instances = '|'.join(map(str, disco_inst()))
    for chaine in instances.split('|'):
        param_inst = chaine.split(";")

        db_port = param_inst[0]
        db_instance = param_inst[1]
    
        if ad_realm == 'LOCAL':
            chaine = 'Driver={};Server={},{};UID={};PWD={}'.format(
                db_driver, hostname, db_port, db_username, db_password)
            cnxn = pyodbc.connect(chaine)
        else:
            isql_host = '{}.{},{}'.format(hostname, ad_realm, db_port)
            chaine = 'DRIVER={};SERVER={};Trusted_Connection=yes'.format(
                db_driver, isql_host)
            cnxn = pyodbc.connect(chaine)
        # Initialisation du curseur.
        cursor = cnxn.cursor()
        get_mssql_jobs_status()
    
# Une fois le nom des jobs récupérés, on créer ou écrase le fichier JSON.

#with open("{}{}{}{}{}{}".format(output_directory, '/', hostname, '_', 'jobs', '.json'), 'w+') as outfile:
#    json.dump({"data": data}, outfile)
#    outfile.write("\n")
        print(json.dumps({"data": data}, indent=4))
