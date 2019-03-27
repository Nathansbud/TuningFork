import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np
import math


tree = ET.parse("/Users/zackamiton/Music/iTunes/iTunes Library.xml")
root = tree.getroot()
track_list = root[0][15]
arr = []
plt.style.use("seaborn")

for elem in track_list:
    play_count = ""
    track_name = ""
    index = 0
    c = {}

    if elem.tag == "dict":
        for i in range(0, len(elem)): #not a python programmer, sue me
            if elem[i].tag == "key":
                c[elem[i].text] = elem[i+1].text
        if "Play Count" not in c:
            c["Play Count"] = "0"
        if "Podcast" not in c:
            arr.append(c)

arr.sort(key=lambda r: int(r["Play Count"]))

for a in arr:
    print(a["Name"] + ": " + a["Play Count"])

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
    # plot_normal_plays()
    plt.scatter(val_list, freq_list)
    plt.show()
    pass