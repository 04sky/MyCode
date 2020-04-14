public class ReenterLockCondition implements Runnable{
    private static ReentrantLock reentrantLock = new ReentrantLock();
    private static Condition condition = reentrantLock.newCondition();
    public static void main(String[] args){
        ReenterLockCondition main = new ReenterLockCondition();
        new Thread(main).start();
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        reentrantLock.lock();
        condition.signal();
        reentrantLock.unlock();
    }

    @Override
    public void run() {
        reentrantLock.lock();
        try {
            condition.await();
            System.out.println("执行完成.");
        } catch (InterruptedException e) {
            e.printStackTrace();
        } finally {
            reentrantLock.unlock();
        }

    }
}