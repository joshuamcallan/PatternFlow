"""
Model Architecture of the Improved Unet

@author Jian Yang Lee
@email jianyang.lee@uqconnect.edu.au
"""

import tensorflow as tf
from tensorflow.python.keras.layers import Add, BatchNormalization, Dropout, Input, Conv2D, UpSampling2D, Conv2DTranspose, Concatenate
from tensorflow.python.keras.layers.advanced_activations import LeakyReLU
from tensorflow.python.keras.models import Model

def context_module(input, filters):
    """[summary]

    Args:
        input ([type]): [description]
        filters ([type]): [description]

    Returns:
        [type]: [description]
    """
    conv_one = Conv2D(filters, kernel_size=3, padding="same", activation=LeakyReLU(alpha=0.1))(input)
    conv_one_batch = BatchNormalization()(conv_one)
    drop_one = Dropout(0.3)(conv_one_batch)
    conv_two = Conv2D(filters, kernel_size=3, padding="same", activation=LeakyReLU(alpha=0.1))(drop_one)
    return conv_two

def localisation_module(input, filters):
    """[summary]

    Args:
        input ([type]): [description]
        filters ([type]): [description]

    Returns:
        [type]: [description]
    """
    conv1 = Conv2D(filters, 3, padding="same", activation=LeakyReLU(alpha=0.1))(input)
    conv1_batch = BatchNormalization()(conv1)
    conv2 = Conv2D(filters, 1, padding="same", activation=LeakyReLU(alpha=0.1))(conv1_batch)

    return conv2



def model(height, width, input_channel, desired_channnel):
    """
    [Add docstrings]
    """
    input = Input((height, width, input_channel))

    ## ENCODING
    # layer 1
    conv1 = Conv2D(16, kernel_size=3, padding="same", activation=LeakyReLU(alpha=0.1))(input)
    context1 = context_module(conv1, 16)
    layer1 = tf.math.add(conv1, context1)


    # layer 2
    conv2 = Conv2D(32, kernel_size=3, strides=(2, 2), padding="same", activation=LeakyReLU(alpha=0.1))(layer1)
    context2 = context_module(conv2, 32)
    layer2 = Add()([conv2, context2])
    layer2 = tf.math.add(conv2, context2)


    # layer 3
    conv3 = Conv2D(64, kernel_size=3, strides=(2, 2), padding="same", activation=LeakyReLU(alpha=0.1))(layer2)
    context3 = context_module(conv3, 64)
    layer3 = tf.math.add(conv3, context3)


    # layer 4
    conv4 = Conv2D(128, kernel_size=3, strides=(2, 2), padding="same", activation=LeakyReLU(alpha=0.1))(layer3)
    context4 = context_module(conv4, 128)
    layer4 = tf.math.add(conv4, context4)

    ## BRIDGE
    conv_bridge = Conv2D(filters=256, kernel_size=3, strides=(2, 2), padding="same", activation=LeakyReLU(alpha=0.1))(layer4)
    context_bridge = context_module(conv_bridge, 256)
    bridge = tf.math.add(conv_bridge, context_bridge)

    upsample_bridge = Conv2DTranspose(filters=128, kernel_size=3, strides=(2, 2), padding="same")(bridge)

    ## DECODING
    # layer 4
    concat_1 = Concatenate()([upsample_bridge, layer4])
    localized_1 = localisation_module(concat_1, 128)
    upsample_1 = Conv2DTranspose(filters=64, kernel_size=(3, 3), strides=2, padding="same")(localized_1)

    # layer 3
    concat_2 = Concatenate()([upsample_1, layer3])
    localized_2 = localisation_module(concat_2, 64)
    upsample_2 = Conv2DTranspose(filters=32, kernel_size=(3, 3), strides=2, padding="same")(localized_2)

    # segment and upscale
    segment_1 = Conv2D(64, kernel_size=(1, 1), padding="same")(localized_2)
    upscale_1 = UpSampling2D((2, 2))(segment_1)

    # layer 2
    concat_3 = Concatenate()([upsample_2, context2])
    localized_3 = localisation_module(concat_3, 32)
    upsample_3 = Conv2DTranspose(filters=16, kernel_size=(3, 3), strides=2, padding="same")(localized_3)

    # element-wise sum with upscale_1 and upscale localized 3 
    segment_2 = Conv2D(64, kernel_size=(1, 1), padding="same")(localized_3)
    sum_1 = tf.math.add(upscale_1, segment_2)
    upscale_2 = UpSampling2D((2, 2))(sum_1)

    # layer 1
    concat_4 = Concatenate()([upsample_3, context1])
    conv_last = Conv2D(32, kernel_size=3, padding="same", activation=LeakyReLU(alpha=0.1))(concat_4)

    # segment and element-wise sum
    segment_3 = Conv2D(64, kernel_size=(1, 1), padding="same")(conv_last)
    sum_2 = tf.math.add(upscale_2, segment_3)


    output = Conv2D(desired_channnel, (1, 1), activation="softmax")(sum_2)

    improved_model = Model(input, output)

    return improved_model



    # segmentation with filter size 2 (for channel) and kernel size of 1 (removes the height and width )

