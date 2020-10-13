# coding=utf-8
import csv, os

def collect_host_service(type, file="/usr/local/nagios/var/status.dat"):

    notif0_hosts = []
    host_index = []
    comment_list = []

    with open(file, "r") as f:
        text = f.readlines()
        f.seek(0)
        notif_index = [i for (i,line) in enumerate(f) if line.strip("\t").strip("\n") == type]
            
        for i in notif_index:
            while text[i].strip("\n") != "hoststatus {" and text[i].strip("\n") != "servicestatus {":
                i -= 1 
                continue
            host_index.append(i)    
    
        for i in host_index:
            host = (tuple(text[i + 1].strip("\t").strip("\n").split("=")))
            service = (tuple(text[i + 2].strip("\t").strip("\n").split("=")))
            if service[0] != 'service_description':
                service = ('service_description', 'host')
            comment = ('comment', 'none')
            notif0_hosts.append(dict([host,service, comment]))
        
        f.seek(0)
        comment_index = [i for (i,line) in enumerate(f) if line.strip("\n") == "hostcomment {" or line.strip("\n") == "servicecomment {"]
        for i in comment_index:
            host = (tuple(text[i + 1].strip("\t").strip("\n").split("=")))
            service = (tuple(text[i + 2].strip("\t").strip("\n").split("=")))
            if service[0] != 'service_description':
                service = ('service_description', 'host')
            while text[i].strip("\n").__contains__("comment_data") == False:
                i += 1 
                continue
            comment = (tuple(text[i].strip("\t").strip("\n").split("=", 1)))
            comment_list.append(dict([host, service, comment]))
    
    for comment in comment_list:
        for host in notif0_hosts:
            if comment['host_name'] == host['host_name'] and comment['service_description'] == host['service_description']:
                host.update({"comment": comment['comment_data']})
    
    return notif0_hosts

def create_rapport(type):

    keys = ['host_name', 'service_description', 'comment']
    
    if type == "denotif":
        notif0_hosts = collect_host_service(type="notifications_enabled=0")
        file = "rapport_notif_disable.csv"
    if type == "deactif":
        notif0_hosts = collect_host_service(type="active_checks_enabled=0")
        file = "rapport_sonde_disable.csv"

    with open(file, "w+") as csv_file:
        writer = csv.DictWriter(csv_file, delimiter=';', fieldnames=keys)
        #writer.writeheader()
        headers = {}
        for n in writer.fieldnames:
            headers [n] = n
        writer.writerow(headers)
        for data in notif0_hosts:
            writer.writerow(data)

def send_email():
    attachment = "rapport_notif_disable.csv,rapport_sondes_notif_disable.csv"
    msg = "Rapport des sondes dénotifiées et désactivées"
    emails = "b.omaradil@gmail.com"
    sender = "nagios@chantiers-atlantique.com"
    
    os.system('/bin/mail -a {0} -s "{1}" -r {2} {3} < /dev/null'.format(attachment, msg, sender, emails))


if __name__ == "__main__":
    create_rapport(type="denotif")
    create_rapport(type="deactif")
    send_email()
