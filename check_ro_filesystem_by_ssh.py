#!/usr/bin/env python

import os
import sys
import subprocess, json

output_directory = '/usr/lib/zabbix/externalscripts/temp'
zabbix_sender = '/usr/bin/zabbix_sender -c /etc/zabbix/zabbix_agentd.conf'
zbx_proxy_ip = '127.0.0.1'
zbx_proxy_port = '10052'

def send_to_zabbix(zbx_key_name, param,  value):
    key = '{}[{}]'.format(zbx_key_name, param, value)
    os.system('{} -s {} --key "{}" --value "{}" -z "{}" -p "{}" > /dev/null'.format(
        zabbix_sender, hostname, key, value, zbx_proxy_ip, zbx_proxy_port))

hostname = sys.argv[1]
user = sys.argv[2]
key = sys.argv[3]

def get_fs():
    # We are looking for such lines:
    #/dev/sda5 /media/ntfs fuseblk rw,nosuid,nodev,noexec,relatime,user_id=0,group_id=0,default_permissions,allow_other,blksize=4096 0 0
    #/dev/sdb1 /media/bigdata ext3 rw,relatime,errors=continue,barrier=1,data=ordered 0 0

    # Beware of the export!
    cmd = 'export LC_LANG=C && unset LANG && grep ^/dev < /proc/mounts'
    ssh = subprocess.Popen(("ssh -o 'StrictHostKeyChecking=no' -i {} {}@{} {}".format(key, user, hostname, cmd)), shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout = ssh.stdout.readlines()

    bad_fs = []
    lines = [line for line in stdout]
    # Let's parse al of this
    for line in lines:
        line = line.strip()
        if not line:
            continue
        tmp = line.split(' ')
        opts = tmp[3]
        F = opts.split(',')
        name = tmp[1]
        zbx_key_name = 'zs.fs.discovery'
        send_to_zabbix(zbx_key_name, name, F[0])
        bad_fs.append({'{#FS}': name})

    return bad_fs

if __name__ == '__main__':

    bad_fs = get_fs()


#with open("{}{}{}{}{}{}".format(output_directory, '/', hostname, '_', 'read_only_fs', '.json'), 'w+') as outfile:
#    json.dump({"data": bad_fs}, outfile)
#    outfile.write("\n")
print(json.dumps({"data": bad_fs}, indent=4))
