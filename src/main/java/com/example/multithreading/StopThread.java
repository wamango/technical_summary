package com.example.multithreading;

/**
 * 通过一个线程让另外一个线程停止
 *
 * @author dzm
 * @create 2019-01-25 15:10
 **/
public class StopThread {
    //volatile保证了可见性，让后台线程能看到主线程修改的值；但是它并不保证原子性
    private static volatile boolean stopRequested;

//    public static void main(String[] args)throws InterruptedException {
//        Thread backgroundTread = new Thread(new Runnable() {
//            @Override
//            public void run() {
//                int i = 0;
//                while (!stopRequested){
//                    i++;
//                }
//            }
//        });
//        backgroundTread.start();
//        //线程睡眠一秒
//        TimeUnit.SECONDS.sleep(1);
//        stopRequested = true;
//    }
}
