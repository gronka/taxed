sudo apt install python3 python3-venv libaugeas0
sudo python3 -m venv /opt/certbot/
sudo /opt/certbot/bin/pip install --upgrade pip
#sudo /opt/certbot/bin/pip install certbot certbot-apache
sudo /opt/certbot/bin/pip install certbot certbot-nginx
sudo ln -s /opt/certbot/bin/certbot /usr/bin/certbot

#sudo certbot --apache
#sudo certbot --apache -d example.com -d www.example.com
sudo certbot --nginx
#OR
sudo certbot --nginx -d fairlytaxed.com -d www.fairlytaxed.com
#sudo certbot certonly --apache
#sudo certbot certonly --nginx


#After you install a Let’s Encrypt certificate on your Ubuntu Certbot setup, you can test your website SSL status at https://WhyNoPadlock.com to identify mixed content errors.
#
#The certificate files for each domain is stored in:

#cd /etc/letsencrypt/live

#Let’s Encrypt certificates expire after 90 days. To prevent SSLs from expiring, Certbot checks your SSL status twice a day and renews certificates expiring within thirty days. You can view settings with Systemd or cron.d.

#systemctl show certbot.timer

#cat /etc/cron.d/certbot

#Ensure the renewal process works:

#sudo certbot renew --dry-run
