# -*- coding: utf-8 -*-
from kubernetes import client, config
import yaml


def kuberobj(cli, class_name):
    """
    :param cli:
    :param class_name:
    :return:
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            obj = getattr(cli, class_name)
            return func(obj=obj, *args, **kwargs)

        return wrapper

    return decorator


class PyKubernetes:

    def login(self, pkey):
        config.load_kube_config(config_file=pkey)

    @kuberobj(cli=client, class_name='AppsV1api')
    def get_all_service(self, obj):
        return obj.list_service_for_all_namespaces()

    @kuberobj(cli=client, class_name='AppsV1api')
    def has_service(self, namespace, service, obj):
        """
        :param namespace:
        :param service:
        :param obj:
        :return:
        """
        service_data = obj.list_namespaced_service(namespace=namespace)
        service_list = [value.metadata.name for value in service_data.items]
        if service in service_list:
            return True
        else:
            return False

    @kuberobj(cli=client, class_name='AppsV1api')
    def has_deployment(self, namespace, deploy, obj):
        service_data = obj.list_namespaced_deployment(namespace=namespace)
        service_list = [value.metadata.name for value in service_data.items]
        if deploy in service_list:
            return True
        else:
            return False

    @kuberobj(cli=client, class_name='AppsV1api')
    def apply_deployment(self, data, namespace, name, obj):
        """
        :param data:
        :param namespace:
        :param name:
        :param obj:
        :return:
        """
        if self.has_deployment(namespace=namespace, deploy=name):
            obj.patch_namespaced_deployment(body=data, namespace=namespace, name=name)
        else:
            obj.create_namespaced_deployment(body=data, namespace=namespace)

    @kuberobj(cli=client, class_name='AppsV1api')
    def apply_service(self, data, namespace, name, obj):
        """
        :param data:
        :param namespace:
        :param name:
        :param obj:
        :return:
        """
        if self.has_service(service=name, namespace=namespace):
            obj.patch_namespaced_service(body=data, namespace=namespace, name=name)
        else:
            obj.create_namespaced_service(body=data, namespace=namespace)

    @kuberobj(cli=client, class_name='AppsV1api')
    def get_all_nodes(self, obj):
        """
        :rtype: V1NodeList
        """
        return obj.list_node()

    def get_all_nodes_name(self):
        """
        :rtype: list
        """
        names = []
        for item in self.get_all_nodes().items:
            names.append(item.metadata.name)

        return names

    @kuberobj(cli=client, class_name='AppsV1api')
    def push_node_label_value(self, node, label, value, obj):
        """
        :param node:
        :param label:
        :param value:
        :param obj:
        :return:
        """
        body = {
            "metadata": {
                "labels": {
                    label: value
                }
            }
        }

        if node in self.get_all_nodes_name():
            obj.patch_node(node, body)
            return True
        else:
            return False

    @kuberobj(cli=client, class_name='CoreV1api')
    def create_namespaced_service_account(self, obj, body, namespace='kube-system', **kwargs):
        obj.create_namespaced_service_account(
            body=body,
            namespace=namespace,
            **kwargs
        )
