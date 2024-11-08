from .components import ComponentMeta

cheetah_linr_cpn_meta = ComponentMeta("CheetahHeteroLinR")

@cheetah_linr_cpn_meta.bind_param
def cheetah_linr_param():
    from federatedml.param.linear_regression_param import LinearParam

    return LinearParam


@cheetah_linr_cpn_meta.bind_runner.on_guest
def cheetah_linr_runner_guest():
    from federatedml.linear_model.linear_regression.cheetah_hetero_linear_regression.hetero_linr_guest import HeteroLinRGuest

    return HeteroLinRGuest


@cheetah_linr_cpn_meta.bind_runner.on_host
def cheetah_linr_runner_host():
    from federatedml.linear_model.linear_regression.cheetah_hetero_linear_regression.hetero_linr_host import HeteroLinRHost

    return HeteroLinRHost

@cheetah_linr_cpn_meta.bind_runner.on_arbiter
def cheetah_linr_runner_arbiter():
    from federatedml.linear_model.linear_regression.hetero_linear_regression.hetero_linr_arbiter import (
        HeteroLinRArbiter,
    )

    return HeteroLinRArbiter