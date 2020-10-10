import csv


def get_notif_disable(file):
    notif0_hosts = []
    host_list = []
    with open(file, "r", errors='ignore') as f:
        text = f.readlines()
        f.seek(0)
        notif_list = [i for (i,line) in enumerate(f) if line.strip("\t").strip("\n") == "notifications_enabled=0"]    

        for i in notif_list:
            while text[i].strip("\n") != "hoststatus {" and text[i].strip("\n") != "servicestatus {":
                i -= 1 
                continue
            host_list.append(i)    

        for i in host_list:
            host = (tuple(text[i + 1].strip("\t").strip("\n").split("=")))
            service = (tuple(text[i + 2].strip("\t").strip("\n").split("=")))
            if service[0] != 'service_description':
                service = ('service_description', 'host')
            notif0_hosts.append(dict([host,service]))
    return notif0_hosts

def get_comment():
    notif_list = [i for (i,line) in enumerate(f) if line.strip("\n") == "hostcomment {" and line.strip("\n") == "servicecomment {"]
    for i in notif_list:
        

keys = ['host_name', 'service_description']

with open("notif_disable.csv", "w+") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=keys)
    writer.writeheader()
    for data in get_notif_disable(file = "status.dat"):
        writer.writerow(data)


    
