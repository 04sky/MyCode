import java.util.concurrent.CountDownLatch;

public class Main{

    public static void main(String[] args) throws InterruptedException{
        CountDownLatch countDownLatch = new CountDownLatch(6);
        for (int i=1; i<=6; i++) {
            new Thread(() -> {
                System.out.println(Thread.currentThread().getName() + " 国被灭.");
                countDownLatch.countDown();
            }, MyData.get(i).getMsg()).start();
        }

        countDownLatch.await();
        System.out.println("秦国统一六国.");
    }
}
