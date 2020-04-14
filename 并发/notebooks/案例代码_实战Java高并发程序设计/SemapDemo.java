public class SemapDemo implements Runnable{
    private final Semaphore semaphore = new Semaphore(5);

    public static void main(String[] args){
        ExecutorService executorService = Executors.newFixedThreadPool(20);
        final SemapDemo main = new SemapDemo();
        for (int i = 0; i < 20; i++) {
            executorService.submit(main);
        }
    }

    @Override
    public void run() {
        try {
            semaphore.acquire();
            Thread.sleep(2000);
            System.out.println(Thread.currentThread().getId() + " done,");
            semaphore.release();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

    }
}