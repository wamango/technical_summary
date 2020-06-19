package com.example.demo.domain.base;


import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.ToString;

import java.util.concurrent.locks.ReentrantLock;

public class Data {
        @Getter
        private  static int counter = 0;
        private static Object locker = new Object();


        public static int reset() {
            counter = 0;
            return counter;
        }

        public synchronized void wrong() {
            synchronized (locker){
                counter++;
            }
        }

}
