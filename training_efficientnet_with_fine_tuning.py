# --coding:utf-8--
import os
import glob
import matplotlib.pyplot as plt
from multiprocessing import Queue
import shutil
# from IPython.display import Image
# %matplotlib inline

from tensorflow import keras
from keras.models import Model
from tensorflow.tools.api.generator.api.keras import models
from tensorflow.tools.api.generator.api.keras import layers
from tensorflow.tools.api.generator.api.keras import optimizers
from tensorflow.tools.api.generator.api.keras.preprocessing.image import ImageDataGenerator
from keras.layers import Dense, GlobalAveragePooling2D
from efficientnet import EfficientNetB0 as Net                            # Import efficientnet and load the conv base model
from efficientnet import center_crop_and_resize, preprocess_input         # Import efficientnet and load the conv base model
from keras.callbacks import ModelCheckpoint


# Hyper parameters 超参数
batch_size = 16

width = 150
height = 150
epochs = 200
NUM_TRAIN = 2000
NUM_TEST = 1000
dropout_rate = 0.2
input_shape = (height, width, 3)

train_dir = './data/dog_vs_cat_small/train'
validation_dir = './data/dog_vs_cat_small/validation'


def get_nb_files(directory):
    """Get number of files by searching directory recursively"""
    if not os.path.exists(directory):
        return 0
    cnt = 0
    for r, dirs, files in os.walk(directory):
        for dr in dirs:
            cnt += len(glob.glob(os.path.join(r, dr + "/*")))
    return cnt


nb_train_samples = get_nb_files(train_dir)  # 训练样本个数
nb_classes = len(glob.glob(train_dir + "/*"))  # 分类数
nb_validation_samples = get_nb_files(validation_dir)  # 验证集样本个数
nb_epoch = int(epochs)  # epoch数量
batch_size = int(batch_size)




train_datagen = ImageDataGenerator(          # 图像在线数据增强的代码块
      rescale=1./255,
      rotation_range=40,
      width_shift_range=0.2,
      height_shift_range=0.2,
      shear_range=0.2,
      zoom_range=0.2,
      horizontal_flip=True,
      fill_mode='nearest')

# Note that the validation data should not be augmented!
# test_datagen = ImageDataGenerator(rescale=1./255)
# 这里我们使用validation而不用test，且照旧对validation数据集进行和train数据集同等强度的在线数据增强
validation_datagen = ImageDataGenerator(
      rescale=1./255,
      rotation_range=40,
      width_shift_range=0.2,
      height_shift_range=0.2,
      shear_range=0.2,
      zoom_range=0.2,
      horizontal_flip=True,
      fill_mode='nearest')

train_generator = train_datagen.flow_from_directory(
        # This is the target directory
        train_dir,
        # All images will be resized to target height and width.
        target_size=(height, width),
        batch_size=batch_size,
        # Since we use categorical_crossentropy loss, we need categorical labels
        class_mode='categorical')

validation_generator = validation_datagen.flow_from_directory(
        validation_dir,
        target_size=(height, width),
        batch_size=batch_size,
        class_mode='categorical')



conv_base = Net(weights='imagenet', include_top=False, input_shape=input_shape)
# model = add_new_last_layer(conv_base, nb_classes)
model = models.Sequential()
# model.add(layers.Flatten(name="flatten"))
model.add(conv_base)
model.add(layers.GlobalMaxPooling2D(name="gap"))
if dropout_rate > 0:
    model.add(layers.Dropout(dropout_rate, name="dropout_out"))
# model.add(layers.Dense(256, activation='relu', name="fc1"))
model.add(layers.Dense(2, activation='softmax', name="fc_out"))    # 这里的2代表要分类的数目

# model.summary()

# 冻结卷积层不参与训练
conv_base.trainable = False

model.compile(loss='categorical_crossentropy', optimizer=optimizers.RMSprop(lr=2e-5),
              metrics=['acc'])


model.load_weights('./output_model_file/my_model.h5')


# Fine tuning 参考CSDN：https://blog.csdn.net/nima1994/article/details/79952368
# Fine tuning last several layers   以下是Fine-tunning代码块

# multiply_16
# set 'multiply_16' and following layers trainable
conv_base.trainable = True

set_trainable = False
for layer in conv_base.layers:
    if layer.name == 'multiply_16':
        set_trainable = True
    if set_trainable:
        layer.trainable = True
    else:
        layer.trainable = False


model.compile(loss='categorical_crossentropy',
              optimizer=optimizers.RMSprop(lr=2e-5),
              metrics=['acc'])



history_tl = model.fit_generator(       # 开始训练
      train_generator,
      steps_per_epoch= NUM_TRAIN //batch_size,
      # samples_per_epoch=nb_train_samples,
      # steps_per_epoch=nb_train_samples,
      epochs=epochs,
      # callbacks=[checkpoint],
      validation_data=validation_generator,
      validation_steps= NUM_TEST //batch_size,
      # nb_val_samples=nb_validation_samples

      # verbose=1,
      # use_multiprocessing=True,
      # workers=4
)



# os.makedirs("./models", exist_ok=True)
model.save('./models/cats_and_dogs_small.h5')



def plot_training(history):

    acc = history.history['acc']
    val_acc = history.history['val_acc']
    loss = history.history['loss']
    val_loss = history.history['val_loss']

    epochs_x = range(len(acc))

    plt.plot(epochs_x, acc, 'bo', label='Training acc')
    plt.plot(epochs_x, val_acc, 'b', label='Validation acc')
    plt.title('Training and validation accuracy')
    plt.legend()

    plt.figure()

    plt.plot(epochs_x, loss, 'bo', label='Training loss')
    plt.plot(epochs_x, val_loss, 'b', label='Validation loss')
    plt.title('Training and validation loss')
    plt.legend()

    plt.show()

# 训练的acc_loss图
plot_training(history_tl)





