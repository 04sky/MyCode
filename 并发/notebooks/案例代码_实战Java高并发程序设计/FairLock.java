public class FairLock implements Runnable{
    private static ReentrantLock reentrantLock = new ReentrantLock(true);

    public static void main(String[] args){
        FairLock main = new FairLock();
        new Thread(main, "t1").start();
        new Thread(main, "t2").start();
    }

    @Override
    public void run() {
        while(true){
            reentrantLock.lock();
            System.out.println(Thread.currentThread().getName() + "获得了锁.");
            reentrantLock.unlock();
        }

    }
}