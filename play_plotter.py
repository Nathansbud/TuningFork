from parser import parse_itunes_xml
import matplotlib.pyplot as plt
import numpy as np
import math

plt.style.use("seaborn")

arr = parse_itunes_xml()
l = [int(x["Play Count"]) for x in arr]

print(l)

count = 1

val_list = []
freq_list = []

for val in range(1, len(l)):
    if l[val] != l[val - 1] or val == len(l) - 1:
        print(str(l[val - 1]) + ": " + str(count))
        val_list.append(l[val - 1])
        freq_list.append(count)
        count = 1
        # if val == len(l) - 1 and l[val] != l[val - 1]:
        #     print(str(l[val]) + ": " + str(count))
        #     val_list.append(l[val])
        #     freq_list.append(count)

        # just horrible code but it's 11:42 and my brain is asleep, fix this off more elegantly by one later
        #also commented because I know the last song is bonetrousle and a huge outlier; handle this better later, see ^


    else:
        count+=1


def plot_normal_plays(): #not using this function for now because HIGHLY not normal distribution lmao it's poisson
    """
    Plot normal distribution for play count
    """
    x = np.linspace(0, 600, 5000)

    mu = (sum(l)/len(l))
    sigma = math.sqrt(sum([math.pow(v - mu, 2) for v in l])/len(l))

    y = (1 / (np.sqrt(2 * np.pi * np.power(sigma, 2)))) * \
        (np.power(np.e, -(np.power((x - mu), 2) / (2 * np.power(sigma, 2)))))

    plt.plot(x, y)
    plt.show()



if __name__ == "__main__":
    plt.scatter(val_list, freq_list)
    plt.show()
    pass
