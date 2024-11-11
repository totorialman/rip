#include <iostream>

class Deque {
 private:
    int* data;
    int head;
    int tail;
    int cap;
    int size;

    void resize() {
        int new_cap = cap * 2;
        int* new_data = new int[new_cap];

        for (int i = 0; i < size; ++i) {
            new_data[i] = data[(head + i) % cap];
        }

        delete[] data;
        data = new_data;
        cap = new_cap;
        head = 0;
        tail = size;
    }

 public:
    explicit Deque(int start_cap = 4) : head(0), tail(0), size(0), cap(start_cap) {
        data = new int[cap];
    }

    ~Deque() {
        delete[] data;
    }

    void push_front(int value) {
        if (size == cap) resize();
        head = (head - 1 + cap) % cap;
        data[head] = value;
        size++;
    }

    void push_back(int value) {
        if (size == cap) resize();
        data[tail] = value;
        tail = (tail + 1) % cap;
        size++;
    }

    int pop_front() {
        if (size == 0) return -1;
        int value = data[head];
        head = (head + 1) % cap;
        size--;
        return value;
    }

    int pop_back() {
        if (size == 0) return -1;
        tail = (tail - 1 + cap) % cap;
        int value = data[tail];
        size--;
        return value;
    }
};

int main() {
    int n;
    std::cin >> n;

    Deque deque;
    bool is_correct = true;

    for (int i = 0; i < n; ++i) {
        int command, expected_value;
        std::cin >> command >> expected_value;

        int result;
        switch (command) {
            case 1:  
                deque.push_front(expected_value);
                break;
            case 2:  
                result = deque.pop_front();
                if (result != expected_value) is_correct = false;
                break;
            case 3:  
                deque.push_back(expected_value);
                break;
            case 4:  
                result = deque.pop_back();
                if (result != expected_value) is_correct = false;
                break;
        }

        if (!is_correct) {
            std::cout << "NO" << std::endl;
            return 0;
        }
    }

    std::cout << "YES" << std::endl;
    return 0;
}
