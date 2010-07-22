"""These are test functions for hinet.
"""

import py.test
import StringIO
import mdp.hinet as mh
from _tools import *
from mdp import numx_rand

_get_new_flow = lambda: mdp.Flow([
        mdp.nodes.NoiseNode(),
        mdp.nodes.SFANode()])

_get_new_nodes = lambda: [
        mdp.nodes.CuBICANode(input_dim=1, whitened=True),
        mdp.nodes.CuBICANode(input_dim=2, whitened=True),
        mdp.nodes.CuBICANode(input_dim=1, whitened=True),
        ]

_get_sigle_node = lambda: mdp.nodes.CuBICANode(input_dim=2, whitened=True)

NODES = [(mh.FlowNode, [_get_new_flow], None),
         (mh.Layer, [_get_new_nodes], None),
         (mh.CloneLayer, [_get_sigle_node, 2], None),
         ]

def test_FlowNode_training():
    flow = mdp.Flow([mdp.nodes.PolynomialExpansionNode(degree=2),
                     mdp.nodes.PCANode(output_dim=15, reduce=True),
                     mdp.nodes.PolynomialExpansionNode(degree=2),
                     mdp.nodes.PCANode(output_dim=3, reduce=True)])
    flownode = mh.FlowNode(flow)
    x = numx_rand.random([300,20])
    while flownode.get_remaining_train_phase() > 0:
        flownode.train(x)
        flownode.stop_training()
    flownode.execute(x)

def test_FlowNode_trainability():
    flow = mdp.Flow([mdp.nodes.PolynomialExpansionNode(degree=2)])
    flownode = mh.FlowNode(flow)
    assert flownode.is_trainable() is False
    flow = mdp.Flow([mdp.nodes.PolynomialExpansionNode(degree=2),
                     mdp.nodes.PCANode(output_dim=15),
                     mdp.nodes.PolynomialExpansionNode(degree=2),
                     mdp.nodes.PCANode(output_dim=3)])
    flownode = mh.FlowNode(flow)
    assert flownode.is_trainable() is True

def test_FlowNode_invertibility():
    flow = mdp.Flow([mdp.nodes.PolynomialExpansionNode(degree=2)])
    flownode = mh.FlowNode(flow)
    assert flownode.is_invertible() is False
    flow = mdp.Flow([mdp.nodes.PCANode(output_dim=15),
                     mdp.nodes.SFANode(),
                     mdp.nodes.PCANode(output_dim=3)])
    flownode = mh.FlowNode(flow)
    assert flownode.is_invertible() is True

def test_FlowNode_pretrained_node():
    x = numx_rand.random([100,10])
    pretrained_node = mdp.nodes.PCANode(output_dim=6)
    pretrained_node.train(x)
    pretrained_node.stop_training()
    flow = mdp.Flow([pretrained_node,
                     mdp.nodes.PolynomialExpansionNode(degree=2),
                     mdp.nodes.PCANode(output_dim=3)])
    flownode = mh.FlowNode(flow)
    while flownode.get_remaining_train_phase() > 0:
        flownode.train(x)
        flownode.stop_training()
    flownode.execute(x)

def test_FlowNode_pretrained_flow():
    flow = mdp.Flow([mdp.nodes.PolynomialExpansionNode(degree=2),
                     mdp.nodes.PCANode(output_dim=15, reduce=True),
                     mdp.nodes.PolynomialExpansionNode(degree=2),
                     mdp.nodes.PCANode(output_dim=3, reduce=True)])
    flownode = mh.FlowNode(flow)
    x = numx_rand.random([300,20])
    while flownode.get_remaining_train_phase() > 0:
        flownode.train(x)
        flownode.stop_training()
    # build new flownode with the trained nodes
    flownode = mh.FlowNode(flow)
    assert not flownode.is_training()
    flownode.execute(x)

def test_FlowNode_copy1():
    flow = mdp.Flow([mdp.nodes.PCANode(), mdp.nodes.SFANode()])
    flownode = mh.FlowNode(flow)
    flownode.copy()

def test_FlowNode_copy2():
    # Test that the FlowNode copy method delegates to internal nodes.
    class CopyFailException(Exception):
        pass
    class CopyFailNode(mdp.Node):
        def copy(self, protocol=-1):
            raise CopyFailException()
    flow = mdp.Flow([mdp.Node(), CopyFailNode()])
    flownode = mh.FlowNode(flow)
    try:
        flownode.copy()
    except CopyFailException:
        pass
    else:
        assert False, 'Did not raise expected exception.'

def test_Layer():
    node1 = mdp.nodes.PCANode(input_dim=10, output_dim=5)
    node2 = mdp.nodes.PCANode(input_dim=17, output_dim=3)
    node3 = mdp.nodes.PCANode(input_dim=3, output_dim=1)
    x = numx_rand.random([100,30]).astype('f')
    layer = mh.Layer([node1, node2, node3])
    layer.train(x)
    y = layer.execute(x)
    assert layer.dtype == numx.dtype('f')
    assert y.dtype == layer.dtype

def test_Layer_invertibility():
    node1 = mdp.nodes.PCANode(input_dim=10, output_dim=10)
    node2 = mdp.nodes.PCANode(input_dim=17, output_dim=17)
    node3 = mdp.nodes.PCANode(input_dim=3, output_dim=3)
    x = numx_rand.random([100,30]).astype('f')
    layer = mh.Layer([node1, node2, node3])
    layer.train(x)
    y = layer.execute(x)
    x_inverse = layer.inverse(y)
    assert numx.all(numx.absolute(x - x_inverse) < 0.001)

def test_Layer_invertibility2():
    # reduce the dimensions, so input_dim != output_dim
    node1 = mdp.nodes.PCANode(input_dim=10, output_dim=8)
    node2 = mdp.nodes.PCANode(input_dim=17, output_dim=12)
    node3 = mdp.nodes.PCANode(input_dim=3, output_dim=3)
    x = numx_rand.random([100,30]).astype('f')
    layer = mh.Layer([node1, node2, node3])
    layer.train(x)
    y = layer.execute(x)
    layer.inverse(y)

def test_SameInputLayer():
    node1 = mdp.nodes.PCANode(input_dim=10, output_dim=5)
    node2 = mdp.nodes.PCANode(input_dim=10, output_dim=3)
    node3 = mdp.nodes.PCANode(input_dim=10, output_dim=1)
    x = numx_rand.random([100,10]).astype('f')
    layer = mh.SameInputLayer([node1, node2, node3])
    layer.train(x)
    y = layer.execute(x)
    assert layer.dtype == numx.dtype('f')
    assert y.dtype == layer.dtype

def test_CloneLayer():
    node = mdp.nodes.PCANode(input_dim=10, output_dim=5)
    x = numx_rand.random([10,70]).astype('f')
    layer = mh.CloneLayer(node, 7)
    layer.train(x)
    y = layer.execute(x)
    assert layer.dtype == numx.dtype('f')
    assert y.dtype == layer.dtype

def test_SwitchboardInverse1():
    sboard = mh.Switchboard(input_dim=3,
                            connections=[2,0,1])
    assert sboard.is_invertible()
    y = numx.array([[2,3,4],[5,6,7]])
    x = sboard.inverse(y)
    assert numx.all(x == numx.array([[3,4,2],[6,7,5]]))

def testSwitchboardInverse2():
    sboard = mh.Switchboard(input_dim=3,
                            connections=[2,1,1])
    assert not sboard.is_invertible()

## Tests for MeanInverseSwitchboard ##

def test_MeanInverseSwitchboard1():
    sboard = mh.MeanInverseSwitchboard(input_dim=3,
                                       connections=[0,0,2])
    assert sboard.is_invertible()
    y = numx.array([[2,4,3],[1,1,7]])
    x = sboard.inverse(y)
    assert numx.all(x == numx.array([[3,0,3],[1,0,7]]))

def test_MeanInverseSwitchboard2():
    sboard = mh.MeanInverseSwitchboard(input_dim=3,
                                       connections=[1,1,1,2,2])
    assert sboard.is_invertible()
    y = numx.array([[2,4,0,1,1],[3,3,3,2,4]])
    x = sboard.inverse(y)
    assert numx.all(x == numx.array([[0,2,1],[0,3,3]]))

## Tests for ChannelSwitchboard ##

def testOutChannelInput():
    sboard = mh.ChannelSwitchboard(input_dim=6,
                                   connections=[5,5,
                                                0,1],
                                   out_channel_dim=2,
                                   in_channel_dim=2)
    assert numx.all(sboard.get_out_channel_input(0) ==
                    numx.array([5,5]))
    assert numx.all(sboard.get_out_channel_input(1) ==
                    numx.array([0,1]))

def testOutChannelsInputChannels():
    sboard = mh.ChannelSwitchboard(input_dim=6,
                                   connections=[5,5, # out chan 1
                                                0,1], # out chan 2
                                   out_channel_dim=2,
                                   in_channel_dim=2)
    # note that there are 3 input channels
    assert numx.all(sboard.get_out_channels_input_channels(0) ==
                    numx.array([2]))
    assert numx.all(sboard.get_out_channels_input_channels(1) ==
                    numx.array([0]))
    assert numx.all(sboard.get_out_channels_input_channels([0,1]) ==
                    numx.array([0,2]))

## Tests for Rectangular2dSwitchboard ##

def testRect2dRouting1():
    sboard = mh.Rectangular2dSwitchboard(x_in_channels=3,
                                         y_in_channels=2,
                                         in_channel_dim=2,
                                         x_field_channels=2,
                                         y_field_channels=1,
                                         x_field_spacing=1,
                                         y_field_spacing=1)
    assert numx.all(sboard.connections ==
                           numx.array([0, 1, 2, 3, 2, 3, 4, 5, 6, 7,
                                       8, 9, 8, 9, 10, 11]))
    x = numx.array([range(0, sboard.input_dim),
                    range(101, 101+sboard.input_dim)])
    sboard.execute(x)
    # test generated switchboard
    channel_sboard = sboard.get_out_channel_node(0)
    channel_sboard.execute(x)

def testRect2dRouting2():
    sboard = mh.Rectangular2dSwitchboard(x_in_channels=2,
                                         y_in_channels=4,
                                         in_channel_dim=1,
                                         x_field_channels=1,
                                         y_field_channels=2,
                                         x_field_spacing=1,
                                         y_field_spacing=2)
    assert numx.all(sboard.connections ==
                    numx.array([0, 2, 1, 3, 4, 6, 5, 7]))
    x = numx.array([range(0, sboard.input_dim),
                    range(101, 101+sboard.input_dim)])
    sboard.execute(x)
    # test generated switchboard
    channel_sboard = sboard.get_out_channel_node(0)
    channel_sboard.execute(x)

def testRect2dRouting3():
    sboard = mh.Rectangular2dSwitchboard(x_in_channels=2,
                                         y_in_channels=4,
                                         in_channel_dim=1,
                                         x_field_channels=2,
                                         y_field_channels=2,
                                         x_field_spacing=1,
                                         y_field_spacing=2)
    assert (sboard.connections ==
            numx.array([0, 1, 2, 3, 4, 5, 6, 7])).all()

def testRect2dRouting4():
    sboard = mh.Rectangular2dSwitchboard(x_in_channels=4,
                                         y_in_channels=4,
                                         in_channel_dim=1,
                                         x_field_channels=3,
                                         y_field_channels=2,
                                         x_field_spacing=1,
                                         y_field_spacing=2)
    assert (sboard.connections ==
            numx.array([0, 1, 2, 4, 5, 6,
                        1, 2, 3, 5, 6, 7,
                        8, 9, 10, 12, 13, 14,
                        9, 10, 11, 13, 14, 15])).all()

def testRect2d_get_out_channel_node():
    sboard = mh.Rectangular2dSwitchboard(x_in_channels=5,
                                         y_in_channels=4,
                                         in_channel_dim=2,
                                         x_field_channels=3,
                                         y_field_channels=2,
                                         x_field_spacing=1,
                                         y_field_spacing=2)
    x = numx.array([range(0, sboard.input_dim),
                    range(101, 101+sboard.input_dim)])
    y = sboard.execute(x)
    # routing layer
    nodes = [sboard.get_out_channel_node(index)
             for index in xrange(sboard.output_channels)]
    layer = mh.SameInputLayer(nodes)
    layer_y = layer.execute(x)
    assert (y == layer_y).all()

def test_Rect2d_exception_1():
    bad_args = dict(x_in_channels=12,
                    y_in_channels=8,
                    x_field_channels=4,
                    # this is the problematic value:
                        y_field_channels=3,
                    x_field_spacing=2,
                    y_field_spacing=2,
                    in_channel_dim=3,
                    ignore_cover=False)
    py.test.raises(mh.Rectangular2dSwitchboardException,
                   'mh.Rectangular2dSwitchboard(**bad_args)')

def test_Rect2d_exception_2():
    bad_args = dict(x_in_channels=12,
                    y_in_channels=8,
                    x_field_channels=4,
                    # this is the problematic value:
                        y_field_channels=9,
                    x_field_spacing=2,
                    y_field_spacing=2,
                    in_channel_dim=3,
                    ignore_cover=False)
    py.test.raises(mh.Rectangular2dSwitchboardException,
                   'mh.Rectangular2dSwitchboard(**bad_args)')

def test_Rect2d_exception_3():
    bad_args = dict(x_in_channels=12,
                    y_in_channels=8,
                    x_field_channels=4,
                    # this is the problematic value:
                        y_field_channels=9,
                    x_field_spacing=2,
                    y_field_spacing=2,
                    in_channel_dim=3,
                    ignore_cover=True)
    py.test.raises(mh.Rectangular2dSwitchboardException,
                   'mh.Rectangular2dSwitchboard(**bad_args)')

## Tests for DoubleRect2dSwitchboard ##

def test_Rect_double_routing_1():
    sboard = mh.DoubleRect2dSwitchboard(x_in_channels=4,
                                        y_in_channels=4,
                                        in_channel_dim=1,
                                        x_field_channels=2,
                                        y_field_channels=2)
    assert (sboard.connections ==
            numx.array([0,1,4,5, 2,3,6,7, 8,9,12,13, 10,11,14,15,
                        # uneven fields
                        5,6,9,10])).all()
    x = numx.array([range(0, sboard.input_dim),
                    range(101, 101+sboard.input_dim)])
    sboard.execute(x)

def test_Rect_double_routing_2():
    sboard = mh.DoubleRect2dSwitchboard(x_in_channels=6,
                                        y_in_channels=4,
                                        in_channel_dim=1,
                                        x_field_channels=2,
                                        y_field_channels=2)
    assert (sboard.connections ==
            numx.array([0,1,6,7, 2,3,8,9, 4,5,10,11, 12,13,18,19,
                        14,15,20,21, 16,17,22,23,
                        # uneven fields
                        7,8,13,14, 9,10,15,16])).all()
    x = numx.array([range(0, sboard.input_dim),
                    range(101, 101+sboard.input_dim)])
    sboard.execute(x)

def test_Rect_double_routing_3():
    sboard = mh.DoubleRect2dSwitchboard(x_in_channels=4,
                                        y_in_channels=6,
                                        in_channel_dim=1,
                                        x_field_channels=2,
                                        y_field_channels=2)
    assert (sboard.connections ==
            numx.array([0,1,4,5, 2,3,6,7, 8,9,12,13, 10,11,14,15,
                        16,17,20,21, 18,19,22,23,
                        # uneven fields
                        5,6,9,10, 13,14,17,18])).all()
    x = numx.array([range(0, sboard.input_dim),
                    range(101, 101+sboard.input_dim)])
    sboard.execute(x)

## Tests for DoubleRhomb2dSwitchboard ##

def test_DoubleRhomb_routing_1():
    sboard = mh.DoubleRhomb2dSwitchboard(x_long_in_channels=3,
                                         y_long_in_channels=2,
                                         diag_field_channels=2,
                                         in_channel_dim=1)
    assert (sboard.connections ==
            numx.array([1,6,7,4])).all()
    x = numx.array([range(0, sboard.input_dim),
                    range(101, 101+sboard.input_dim)])
    sboard.execute(x)

def test_DoubleRhomd_routing_2():
    sboard = mh.DoubleRhomb2dSwitchboard(x_long_in_channels=2,
                                         y_long_in_channels=3,
                                         diag_field_channels=2,
                                         in_channel_dim=1)
    assert (sboard.connections ==
            numx.array([6,2,3,7])).all()
    x = numx.array([range(0, sboard.input_dim),
                    range(101, 101+sboard.input_dim)])
    sboard.execute(x)

def test_DoubleRhomd_routing_3():
    sboard = mh.DoubleRhomb2dSwitchboard(x_long_in_channels=4,
                                         y_long_in_channels=2,
                                         diag_field_channels=2,
                                         in_channel_dim=1)
    assert (sboard.connections ==
            numx.array([1,8,9,5, 2,9,10,6])).all()
    x = numx.array([range(0, sboard.input_dim),
                    range(101, 101+sboard.input_dim)])
    sboard.execute(x)

def test_DoubleRhomd_routing_4():
    sboard = mh.DoubleRhomb2dSwitchboard(x_long_in_channels=2,
                                         y_long_in_channels=4,
                                         diag_field_channels=2,
                                         in_channel_dim=1)
    assert (sboard.connections ==
            numx.array([8,2,3,9, 9,4,5,10])).all()
    x = numx.array([range(0, sboard.input_dim),
                    range(101, 101+sboard.input_dim)])
    sboard.execute(x)

def test_DoubleRhomd_routing_5():
    sboard = mh.DoubleRhomb2dSwitchboard(x_long_in_channels=4,
                                         y_long_in_channels=4,
                                         diag_field_channels=2,
                                         in_channel_dim=1)
    assert (sboard.connections ==
            numx.array([1,16,17,5,
                        2,17,18,6,
                        5,19,20,9,
                        6,20,21,10,
                        9,22,23,13,
                        10,23,24,14])).all()
    x = numx.array([range(0, sboard.input_dim),
                    range(101, 101+sboard.input_dim)])
    sboard.execute(x)

def test_DoubleRhomd_routing_6():
    sboard = mh.DoubleRhomb2dSwitchboard(x_long_in_channels=7,
                                         y_long_in_channels=4,
                                         diag_field_channels=4,
                                         in_channel_dim=1)
    x = numx.array([range(0, sboard.input_dim),
                    range(101, 101+sboard.input_dim)])
    sboard.execute(x)

def test_DoubleRhomd_routing_7():
    sboard = mh.DoubleRhomb2dSwitchboard(x_long_in_channels=4,
                                         y_long_in_channels=7,
                                         diag_field_channels=4,
                                         in_channel_dim=1)
    x = numx.array([range(0, sboard.input_dim),
                    range(101, 101+sboard.input_dim)])
    sboard.execute(x)

def test_DoubleRhomd_routing_8():
    sboard = mh.DoubleRhomb2dSwitchboard(x_long_in_channels=6,
                                         y_long_in_channels=7,
                                         diag_field_channels=4,
                                         in_channel_dim=1)
    x = numx.array([range(0, sboard.input_dim),
                    range(101, 101+sboard.input_dim)])
    sboard.execute(x)

def test_hinet_simple_net():
    switchboard = mh.Rectangular2dSwitchboard(x_in_channels=12,
                                              y_in_channels=8,
                                              x_field_channels=4,
                                              y_field_channels=4,
                                              x_field_spacing=2,
                                              y_field_spacing=2,
                                              in_channel_dim=3)

    node = mdp.nodes.PCANode(input_dim=4*4*3, output_dim=5)
    flownode = mh.FlowNode(mdp.Flow([node,]))
    layer = mh.CloneLayer(flownode, switchboard.output_channels)
    flow = mdp.Flow([switchboard, layer])
    x = numx_rand.random([5, switchboard.input_dim])
    flow.train(x)

def pytest_funcarg__noisenode(request):
    return mdp.nodes.NoiseNode(input_dim=20*20,
                               noise_args=(0, 0.0001))

def test_SFA_net(noisenode):
    sfa_node = mdp.nodes.SFANode(input_dim=20*20, output_dim=10, dtype='f')
    switchboard = mh.Rectangular2dSwitchboard(x_in_channels=100,
                                              y_in_channels=100,
                                              x_field_channels=20,
                                              y_field_channels=20,
                                              x_field_spacing=10,
                                              y_field_spacing=10)
    flownode = mh.FlowNode(mdp.Flow([noisenode, sfa_node]))
    sfa_layer = mh.CloneLayer(flownode, switchboard.output_channels)
    flow = mdp.Flow([switchboard, sfa_layer])
    train_gen = numx.cast['f'](numx_rand.random((3, 10, 100*100)))
    flow.train([None, train_gen])

def testHiNetHTML(noisenode):
    # create some flow for testing
    sfa_node = mdp.nodes.SFANode(input_dim=20*20, output_dim=10)
    switchboard = mh.Rectangular2dSwitchboard(x_in_channels=100,
                                              y_in_channels=100,
                                              x_field_channels=20,
                                              y_field_channels=20,
                                              x_field_spacing=10,
                                              y_field_spacing=10)
    flownode = mh.FlowNode(mdp.Flow([noisenode, sfa_node]))
    sfa_layer = mh.CloneLayer(flownode, switchboard.output_channels)
    flow = mdp.Flow([switchboard, sfa_layer])
    # create dummy file to write the HTML representation
    html_file = StringIO.StringIO()
    hinet_html = mdp.hinet.HiNetHTMLTranslator()
    hinet_html.write_flow_to_file(flow, html_file)
    html_file.close()

def testHiNetXHTML():
    # create some flow for testing
    sfa_node = mdp.nodes.SFANode(input_dim=20*20, output_dim=10)
    flow = mdp.Flow([sfa_node])
    # create dummy file to write the HTML representation
    html_file = StringIO.StringIO()
    hinet_html = mdp.hinet.HiNetXHTMLTranslator()
    hinet_html.write_flow_to_file(flow, html_file)
    html_file.close()
