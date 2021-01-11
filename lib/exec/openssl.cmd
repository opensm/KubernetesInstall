/usr/bin/openssl genrsa -out {1}/ca.key 2048
/usr/bin/openssl req -x509 -new -nodes -key {1}/ca.key -config {0}/openssl.conf -subj "/CN=kubernetes-ca" -extensions v3_ca -out {1}/ca.crt -days 10000
/usr/bin/openssl genrsa -out {1}/etcd/ca.key 2048
/usr/bin/openssl req -x509 -new -nodes -key {1}/etcd/ca.key -config {0}/openssl.conf -subj "/CN=etcd-ca" -extensions v3_ca -out {1}/etcd/ca.crt -days 10000
/usr/bin/openssl genrsa -out {1}/front-proxy-ca.key 2048
/usr/bin/openssl req -x509 -new -nodes -key {1}/front-proxy-ca.key -config {0}/openssl.conf -subj "/CN=kubernetes-ca" -extensions v3_ca -out {1}/front-proxy-ca.crt -days 10000
/usr/bin/openssl genrsa -out {1}/apiserver-etcd-client.key 2048
/usr/bin/openssl req -new -key {1}/apiserver-etcd-client.key -subj "/CN=apiserver-etcd-client/O=system:masters" -out {1}/apiserver-etcd-client.csr
/usr/bin/openssl x509 -in {1}/apiserver-etcd-client.csr -req -CA {1}/etcd/ca.crt -CAkey {1}/etcd/ca.key -CAcreateserial -extensions v3_req_etcd -extfile {0}/openssl.conf -out {1}/apiserver-etcd-client.crt -days 10000
/usr/bin/openssl genrsa -out {1}/etcd/server.key 2048
/usr/bin/openssl req -new -key {1}/etcd/server.key -subj "/CN=etcd-server" -out {1}/etcd/server.csr
/usr/bin/openssl x509 -in {1}/etcd/server.csr -req -CA {1}/etcd/ca.crt -CAkey {1}/etcd/ca.key -CAcreateserial -extensions v3_req_etcd -extfile {0}/openssl.conf -out {1}/etcd/server.crt -days 10000
/usr/bin/openssl genrsa -out {1}/etcd/peer.key 2048
/usr/bin/openssl req -new -key {1}/etcd/peer.key -subj "/CN=etcd-peer" -out {1}/etcd/peer.csr
/usr/bin/openssl x509 -in {1}/etcd/peer.csr -req -CA {1}/etcd/ca.crt -CAkey {1}/etcd/ca.key -CAcreateserial -extensions v3_req_etcd -extfile {0}/openssl.conf -out {1}/etcd/peer.crt -days 10000
/usr/bin/openssl genrsa -out {1}/etcd/healthcheck-client.key 2048
/usr/bin/openssl req -new -key {1}/etcd/healthcheck-client.key -subj "/CN=etcd-client" -out {1}/etcd/healthcheck-client.csr
/usr/bin/openssl x509 -in {1}/etcd/healthcheck-client.csr -req -CA {1}/etcd/ca.crt -CAkey {1}/etcd/ca.key -CAcreateserial -extensions v3_req_etcd -extfile {0}/openssl.conf -out {1}/etcd/healthcheck-client.crt -days 1000
/usr/bin/openssl genrsa -out {1}/apiserver.key 2048
/usr/bin/openssl req -new -key {1}/apiserver.key -subj "/CN=kube-apiserver" -config {0}/openssl.conf -out {1}/apiserver.csr
/usr/bin/openssl x509 -req -in {1}/apiserver.csr -CA {1}/ca.crt -CAkey {1}/ca.key -CAcreateserial -days 10000 -extensions v3_req_apiserver -extfile {0}/openssl.conf -out {1}/apiserver.crt
/usr/bin/openssl genrsa -out  {1}/apiserver-kubelet-client.key 2048
/usr/bin/openssl req -new -key {1}/apiserver-kubelet-client.key -subj "/CN=apiserver-kubelet-client/O=system:masters" -out {1}/apiserver-kubelet-client.csr
/usr/bin/openssl x509 -req -in {1}/apiserver-kubelet-client.csr -CA {1}/ca.crt -CAkey {1}/ca.key -CAcreateserial -days 10000 -extensions v3_req_client -extfile {0}/openssl.conf -out {1}/apiserver-kubelet-client.crt
/usr/bin/openssl genrsa -out  {1}/front-proxy-client.key 2048
/usr/bin/openssl req -new -key {1}/front-proxy-client.key -subj "/CN=front-proxy-client" -out {1}/front-proxy-client.csr
/usr/bin/openssl x509 -req -in {1}/front-proxy-client.csr -CA {1}/front-proxy-ca.crt -CAkey {1}/front-proxy-ca.key -CAcreateserial -days 10000 -extensions v3_req_client -extfile {0}/openssl.conf -out {1}/front-proxy-client.crt
/usr/bin/openssl genrsa -out {1}/kube-scheduler.key 2048
/usr/bin/openssl req -new -key {1}/kube-scheduler.key -subj "/CN=system:kube-scheduler" -out {1}/kube-scheduler.csr
/usr/bin/openssl x509 -req -in {1}/kube-scheduler.csr -CA {1}/ca.crt -CAkey {1}/ca.key -CAcreateserial -days 10000 -extensions v3_req_client -extfile {0}/openssl.conf -out {1}/kube-scheduler.crt
/usr/bin/openssl genrsa -out {1}/sa.key 2048
/usr/bin/openssl ecparam -name secp521r1 -genkey -noout -out {1}/sa.key
/usr/bin/openssl ec -in {1}/sa.key -outform PEM -pubout -out {1}/sa.pub
/usr/bin/openssl req -new -sha256 -key {1}/sa.key -subj "/CN=system:kube-controller-manager" -out {1}/sa.csr
/usr/bin/openssl x509 -req -in {1}/sa.csr -CA {1}/ca.crt -CAkey {1}/ca.key -CAcreateserial -days 10000 -extensions v3_req_client -extfile {0}/openssl.conf -out {1}/sa.crt
/usr/bin/openssl genrsa -out {1}/admin.key 2048
/usr/bin/openssl req -new -key {1}/admin.key -subj "/CN=kubernetes-admin/O=system:masters" -out {1}/admin.csr
/usr/bin/openssl x509 -req -in {1}/admin.csr -CA {1}/ca.crt -CAkey {1}/ca.key -CAcreateserial -days 10000 -extensions v3_req_client -extfile {0}/openssl.conf -out {1}/admin.crt