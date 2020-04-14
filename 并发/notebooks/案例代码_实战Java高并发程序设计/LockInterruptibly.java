import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;

public class LockInterruptibly implements Runnable{
    private int type;
    private static ReentrantLock lock1 = new ReentrantLock();
    private static ReentrantLock lock2 = new ReentrantLock();
    private LockInterruptibly(int type) {
        this.type = type;
    }

    public static void main(String[] args) throws InterruptedException{
        Thread t1 = new Thread(new LockInterruptibly(1));
        Thread t2 = new Thread(new LockInterruptibly(2));
        t1.start();t2.start();
        TimeUnit.SECONDS.sleep(4);
        t2.interrupt();
    }

    @Override
    public void run() {

        try {
            if (type == 1) {
                lock1.lockInterruptibly();
                TimeUnit.SECONDS.sleep(2);
                lock2.lockInterruptibly();
            }else{
                lock2.lockInterruptibly();;
                TimeUnit.SECONDS.sleep(2);
                lock1.lockInterruptibly();
            }

        } catch (InterruptedException e) {
            e.printStackTrace();
        } finally {
            if (lock1.isHeldByCurrentThread()) {
                lock1.unlock();
            }
            if (lock2.isHeldByCurrentThread()) {
                lock2.unlock();
            }
            System.out.println(Thread.currentThread().getId() + " 退出了.");
        }

    }
}