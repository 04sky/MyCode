public class TryLock implements Runnable{
    private ReentrantLock reentrantLock = new ReentrantLock();

    public static void main(String[] args) throws InterruptedException{
        TryLock main = new TryLock();
        Thread t1 = new Thread(main);
        Thread t2 = new Thread(main);
        t1.start();
        t2.start();
    }

    @Override
    public void run() {
        try {
            if (reentrantLock.tryLock(5, TimeUnit.SECONDS)) {
                Thread.sleep(6000);
            }else{
                System.out.println("don't get lock");
            }

        } catch (InterruptedException e) {
            e.printStackTrace();
        }finally {
            if (reentrantLock.isHeldByCurrentThread()) {
                reentrantLock.unlock();
            }
        }


    }
}