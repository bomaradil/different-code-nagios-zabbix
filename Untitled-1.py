import csv

file = "status.dat"
notif0_hosts = []
host_index = []
comment_list = []

with open(file, "r", errors='ignore') as f:
    text = f.readlines()
    f.seek(0)
    notif_index = [i for (i,line) in enumerate(f) if line.strip("\t").strip("\n") == "notifications_enabled=0"]    

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
            


keys = ['host_name', 'service_description', 'comment']

with open("notif_disable.csv", "w+") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=keys)
    writer.writeheader()
    for data in notif0_hosts:
        writer.writerow(data)
