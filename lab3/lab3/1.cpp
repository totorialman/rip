#include <iostream>
#include <functional>
#include <cstdlib>
#include <ctime>
#include <utility>

// Функция для разбиения массива методом прохода двумя итераторами
int partition(int arr[], int left, int right, std::function<bool(int, int)> comp) {
    int randomIndex = left + std::rand() % (right - left + 1);
    std::swap(arr[randomIndex], arr[right]);
    int pivot = arr[right];
    int i = right;
    int j = right - 1;

    while (j >= left) {
        if (comp(arr[j], pivot)) {
            --j;
        } else {
            --i;
            std::swap(arr[i], arr[j]);
            --j;
        }
    }
    std::swap(arr[i], arr[right]);
    return i;
}

// Функция для поиска k-го порядкового элемента
int quickSelect(int arr[], int left, int right, int k, std::function<bool(int, int)> comp) {
    while (true) {
        int pivot = partition(arr, left, right, comp);
        if (pivot == k) {
            return arr[pivot];
        } else if (pivot < k) {
            left = pivot + 1;
        } else {
            right = pivot - 1;
        }
    }
}

bool comp(int a, int b) {
    return a < b;
}

int main() {
    std::srand(std::time(0));
    int n;
    std::cin >> n;
    int arr[n];
    for (int i = 0; i < n; ++i) {
        std::cin >> arr[i];
    }
    std::cout << quickSelect(arr, 0, n - 1, n / 10, comp) << std::endl;
    std::cout << quickSelect(arr, 0, n - 1, n / 2, comp) << std::endl;
    std::cout << quickSelect(arr, 0, n - 1, 9 * n / 10, comp) << std::endl;
    return 0;
}
