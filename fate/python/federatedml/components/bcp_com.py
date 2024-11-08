from .components import ComponentMeta

homo_lr_bcp_cpn_meta = ComponentMeta("BCPTest")

@homo_lr_bcp_cpn_meta.bind_param
def homo_lr_bcp_param():
    from federatedml.param.logistic_regression_param import HomoLogisticParam

    return HomoLogisticParam

@homo_lr_bcp_cpn_meta.bind_runner.on_guest
def homo_lr_bcp_runner_guest():
    from federatedml.linear_model.logistic_regression.homo_logistic_regression.homo_lr_guest_bcp import HomoLRGuest

    return HomoLRGuest

@homo_lr_bcp_cpn_meta.bind_runner.on_host
def homo_lr_bcp_runner_host():
    from federatedml.linear_model.logistic_regression.homo_logistic_regression.homo_lr_host_bcp import HomoLRHost

    return HomoLRHost

@homo_lr_bcp_cpn_meta.bind_runner.on_arbiter
def homo_lr_bcp_runnerr_arbiter():
    from federatedml.linear_model.logistic_regression.homo_logistic_regression.homo_lr_arbiter_bcp import HomoLRArbiter

    return HomoLRArbiter