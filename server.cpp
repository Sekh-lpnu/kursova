#include <iostream>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <map>
#include <string>
#include <sstream>
#include <cstring>
#include <windows.h>
#include <iomanip>


#pragma comment(lib, "ws2_32.lib")


class User {
protected:
    std::string username;
    std::string password;
public:
    User(std::string username, std::string password) : username(username), password(password) {}
    virtual void displayUserInfo() = 0;
    virtual std::string getPassword() {
        return this->password;
    }
};


class Client : public User {
private:
    int bestHours;
    int bestMinutes;
    int bestSeconds;
public:
    Client(std::string username, std::string password) : User(username, password)
    {
        this->bestHours = INT_MAX;
        this->bestMinutes = INT_MAX;
        this->bestSeconds = INT_MAX;
    }
    void displayUserInfo() {
        std::cout << "Client Username: " << username << std::endl;
    }
    int getHours() {
        return this->bestHours;
    }
    int getMinutes() {
        return this->bestMinutes;
    }
    int getSeconds() {
        return this->bestSeconds;
    }

    bool isNewResultBetter(int hours, int minutes, int seconds) {
        if (this->bestHours >= hours && (this->bestMinutes > minutes || (this->bestMinutes == minutes && this->bestSeconds >= seconds)))
            return true;
        return false;
    }

    void ChangeValues(int hours, int minutes, int seconds) {
        this->bestHours = hours;
        this->bestMinutes = minutes;
        this->bestSeconds = seconds;
    }
};




std::map<std::string, Client> users;

void handleClientRequest(SOCKET clientSocket) {
    char buffer[1024];
    memset(buffer, 0, sizeof(buffer));

    int bytesRead = recv(clientSocket, buffer, sizeof(buffer) - 1, 0);
    if (bytesRead == SOCKET_ERROR) {
        perror("Error");
        return;
    }

    std::string request(buffer);


    std::istringstream iss(request);
    std::string cmd;
    iss >> cmd;

    if (cmd == "reg") {
        std::string username, password;
        iss >> username >> password;
        if (username != "" && password != "") {
            if (users.find(username) == users.end()) {
                Client newUser(username, password);

                users.insert(std::make_pair(username, newUser));

                std::string response = "Registration was successful!";
                send(clientSocket, response.c_str(), response.length(), 0);
            }
            else {

                std::string response = "Username already taken!";
                send(clientSocket, response.c_str(), response.length(), 0);
            }
        }
    }

    else if (cmd == "log") {
        std::string username, password;
        iss >> username >> password;

        auto value = users.find(username);
        if (value != users.end() && value->second.getPassword() == password) {

            std::string response = "Login was successful!";
            send(clientSocket, response.c_str(), response.length(), 0);
        }
        else {
            std::string response = "Incorrect login or password!";
            send(clientSocket, response.c_str(), response.length(), 0);
        }
    }

    else if (cmd == "end") {
        std::string username, hours, minutes, seconds;
        iss >> username >> hours >> minutes >> seconds;

        auto user = users.find(username);

        if (user != users.end()) {

            int hoursValue = std::stoi(hours);
            int minutesValue = std::stoi(minutes);
            int secondsValue = std::stoi(seconds);

            int oldHours = user->second.getHours();
            int oldMinutes = user->second.getMinutes();
            int oldSeconds = user->second.getSeconds();

            // Якщо рекорд ще не був встановлений (значення INT_MAX), то встановлюємо початковий рекорд 00:00:00
            if (oldHours == INT_MAX && oldMinutes == INT_MAX && oldSeconds == INT_MAX) {
                oldHours = oldMinutes = oldSeconds = 0;
            }

            std::ostringstream oss;
            // Форматуємо години, хвилини і секунди як двоцифрові числа
            oss << std::setw(2) << std::setfill('0') << oldHours << ":"
                << std::setw(2) << std::setfill('0') << oldMinutes << ":"
                << std::setw(2) << std::setfill('0') << oldSeconds;

            std::string formattedRecord = oss.str();

            if (user->second.isNewResultBetter(hoursValue, minutesValue, secondsValue)) {
                user->second.ChangeValues(hoursValue, minutesValue, secondsValue);
                std::string response = "You won and broke a record! Previous record: " + formattedRecord;
                send(clientSocket, response.c_str(), response.length(), 0);
            }
            else {
                std::string response = "You won!";
                send(clientSocket, response.c_str(), response.length(), 0);
            }
        }
    }



    else {
        std::string response = "Invalid command!";
        send(clientSocket, response.c_str(), response.length(), 0);
    }

    closesocket(clientSocket);
}


int Initialize() {
    WSADATA wsaData;
    // Ініціалізуємо Winsock
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cout << "Не вдалося ініціалізувати Winsock.\n";
        return 1;
    }
    // Створюємо серверний сокет
    SOCKET serverSocket = socket(AF_INET, SOCK_STREAM, 0);
    if (serverSocket == INVALID_SOCKET) {
        std::cout << "Не вдалося створити сокет\n";
        WSACleanup();
        return 1;
    }

    sockaddr_in serverAddress{};
    serverAddress.sin_family = AF_INET;
    serverAddress.sin_port = htons(1234);
    serverAddress.sin_addr.s_addr = INADDR_ANY;
    // Прив'язуєсо сокет до порту
    if (bind(serverSocket, reinterpret_cast<sockaddr*>(&serverAddress), sizeof(serverAddress)) == SOCKET_ERROR) {
        std::cout << "Не вдалося прив’язати сокет.\n";
        closesocket(serverSocket);
        WSACleanup();
        return 1;
    }

    // Прослуховуємо підключення
    if (listen(serverSocket, 5) == SOCKET_ERROR) {
        std::cout << "Не вдалося прослухати сокет.\n";
        closesocket(serverSocket);
        WSACleanup();
        return 1;
    }

    std::cout << "Сервер запущено. Прослуховування підключень..." << std::endl;
    // Приймаємо підключення від клієнта
    while (true) {
        sockaddr_in clientAddress{};
        int clientAddressSize = sizeof(clientAddress);
        SOCKET clientSocket = accept(serverSocket, reinterpret_cast<sockaddr*>(&clientAddress), &clientAddressSize);
        if (clientSocket == INVALID_SOCKET) {
            std::cout << "Не вдалося прийняти підключення клієнта.\n";
            continue;
        }
        handleClientRequest(clientSocket);
    }
    closesocket(serverSocket);


    WSACleanup();
}


int main() {
    SetConsoleCP(1251);
    SetConsoleOutputCP(1251);

    if (Initialize())
        return 1;

    return 0;
}
