USE WoW_PL
;


SET XACT_ABORT ON;   -- ka¿dy b³¹d => rollback ca³oœci
BEGIN TRANSACTION;

-- 1) Treœæ misji: usuñ statusy t³umaczeñ (zostaje 0_ORYGINA£ i 4_REFERENCJA)
DELETE FROM dbo.MISJE_STATUSY
WHERE STATUS IN (N'1_PRZET£UMACZONO', N'2_ZREDAGOWANO', N'3_ZATWIERDZONO');
PRINT 'MISJE_STATUSY - usuniêto wierszy: ' + CAST(@@ROWCOUNT AS VARCHAR(20));

-- 2) Dialogi: usuñ statusy t³umaczeñ (zostaje 0_ORYGINA£)
DELETE FROM dbo.DIALOGI_STATUSY
WHERE STATUS IN (N'1_PRZET£UMACZONO', N'2_ZREDAGOWANO', N'3_ZATWIERDZONO');
PRINT 'DIALOGI_STATUSY - usuniêto wierszy: ' + CAST(@@ROWCOUNT AS VARCHAR(20));

-- 3) Wyzeruj hashe EN (reset bazy do wykrywania zmian z wiki)
UPDATE dbo.MISJE_STATUSY   SET HASH_EN = NULL WHERE HASH_EN IS NOT NULL;
PRINT 'MISJE_STATUSY - HASH_EN=NULL w wierszach: ' + CAST(@@ROWCOUNT AS VARCHAR(20));

UPDATE dbo.DIALOGI_STATUSY SET HASH_EN = NULL WHERE HASH_EN IS NOT NULL;
PRINT 'DIALOGI_STATUSY - HASH_EN=NULL w wierszach: ' + CAST(@@ROWCOUNT AS VARCHAR(20));

-- 4) Reset stanu na poziomie misji
UPDATE dbo.MISJE
SET STATUS_MISJI       = 0,
    MISJA_TYTUL_PL     = NULL,
    HASH_EN            = NULL,
    WSKAZNIK_ZGODNOSCI = NULL;
PRINT 'MISJE - zresetowano wierszy: ' + CAST(@@ROWCOUNT AS VARCHAR(20));

-- 5) Wyczyœæ ca³¹ tabelê wskaŸników zgodnoœci
TRUNCATE TABLE dbo.MISJE_WSKAZNIKI_ZGODNOSCI;
PRINT 'MISJE_WSKAZNIKI_ZGODNOSCI - wyczyszczona (TRUNCATE).';

COMMIT TRANSACTION;
PRINT 'GOTOWE - commit. Mo¿na zaczynaæ od nowa.';
