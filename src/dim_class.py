import random
from subprocess import call

class DIM:
    _MS_PER_SEC = 1000

    def __init__(self, external_ip, external_live_port, apache_port, nginx_port, min_switch_time, max_switch_time, iptables_rules):
        self._APACHE_LABEL = "apache"
        self._NGINX_LABEL = "nginx"

        self.EXTERNAL_IP = external_ip
        self.EXTERNAL_LIVE_PORT = external_live_port
        self.APACHE_PORT = apache_port
        self.NGINX_PORT = nginx_port

        self._set_wait_times(min_switch_time, max_switch_time)
        self._restore_iptables_rules(iptables_rules)

        self._live_web_server = self._NGINX_LABEL
        self.local_live_port = self.NGINX_PORT

    def get_live_web_server_label(self):
        return self._live_web_server

    def _restore_iptables_rules(self, iptables_rules):
        with open(iptables_rules, "r") as iptables_rules_file:
            call(["iptables-restore"], stdin=iptables_rules_file)

    def _set_wait_times(self, min_wait, max_wait):
        self._MIN_WAIT_MS = min_wait * self._MS_PER_SEC
        self._MAX_WAIT_MS = max_wait * self._MS_PER_SEC

    def get_wait_time(self):
        rand_ms = random.randint(self._MIN_WAIT_MS, self._MAX_WAIT_MS)
        rand_sec = rand_ms / self._MS_PER_SEC
        return rand_sec

    def make_live(self):
        self._live_web_server = self.select_web_server(self._live_web_server)
        self._remove_port_forwarding_rule()
        self._forward_to_new_port()

    def _remove_port_forwarding_rule(self):
        # deleted rule forwarding port 80 to old_port from nat table
        call(["iptables", "-t", "nat", "-D", "PREROUTING", "-p", "tcp", "-d",
              str(self.EXTERNAL_IP), "--dport", str(self.EXTERNAL_LIVE_PORT), "-j", "DNAT",
              "--to-destination", "127.0.0.1:" + str(self.local_old_port)])

    def _forward_to_new_port(self):
        # Add new rule forwarding port 80 to new_port
        call(["iptables", "-t", "nat", "-A", "PREROUTING", "-p", "tcp", "-d",
              str(self.EXTERNAL_IP), "--dport", str(self.EXTERNAL_LIVE_PORT), "-j", "DNAT",
              "--to-destination", "127.0.0.1:" + str(self.local_live_port)])

    def _get_new_port(self, next_web_server):
        if next_web_server == self._APACHE_LABEL:
            next_port = self.APACHE_PORT
            self.local_old_port = self.NGINX_PORT
        elif next_web_server == self._NGINX_LABEL:
            next_port = self.NGINX_PORT
            self.local_old_port = self.APACHE_PORT
        return next_port

    def select_web_server(self, curr_live_web_server):
        print("Switching web servers...")
        if curr_live_web_server == self._APACHE_LABEL:
            self._live_web_server = self._NGINX_LABEL
        elif curr_live_web_server == self._NGINX_LABEL:
            self._live_web_server = self._APACHE_LABEL

        self.local_live_port = self._get_new_port(self._live_web_server)
        print("New server: ", self._live_web_server, " New port:", self.local_live_port)
        return self._live_web_server
